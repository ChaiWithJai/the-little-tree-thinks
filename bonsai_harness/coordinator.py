from __future__ import annotations

import copy
import threading
import time
import uuid
from collections import OrderedDict
from collections.abc import Callable
from typing import Any

from .domain import validate_corpus
from .state_machine import RunStateMachine


class RunCoordinator:
    """Bounded local job coordinator with an explicit, observable run FSM."""

    def __init__(self, service_factory: Callable[[], Any], *, repository: Any | None = None, trace_store: Any | None = None, max_concurrent: int = 1, retained_jobs: int = 100):
        self.service_factory = service_factory
        self.repository = repository
        self.trace_store = trace_store
        self.retained_jobs = retained_jobs
        self._capacity = threading.Semaphore(max_concurrent)
        self._lock = threading.RLock()
        self._jobs: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self._machines: dict[str, RunStateMachine] = {}
        if repository is not None:
            for job in repository.recover_interrupted_jobs(retained=retained_jobs):
                self._jobs[job["id"]] = job

    def start(self, question: object, corpus: object, case_id: object = None, *, kind: str = "text") -> dict[str, Any]:
        question = str(question or "").strip()
        if not question:
            raise ValueError("A case question is required.")
        corpus = validate_corpus(corpus)
        job_id = uuid.uuid4().hex
        now = time.time()
        job = {
            "id": job_id, "state": "queued", "kind": kind, "question": question, "corpus": corpus,
            "case_id": case_id, "created_at": now, "updated_at": now,
            "failed_stage": None, "error": None, "run": None,
            "events": [{"state": "queued", "at": now}],
        }
        if self.trace_store is not None:
            trace = self.trace_store.start(kind, f"{kind}.run", job_id=job_id, case_id=case_id, input_chars=len(question))
            trace.event("queued")
            job["trace_id"] = trace.id
            job["_trace"] = trace
        with self._lock:
            self._jobs[job_id] = job
            self._machines[job_id] = RunStateMachine()
            self._persist(job)
            while len(self._jobs) > self.retained_jobs:
                expired_id, _ = self._jobs.popitem(last=False)
                self._machines.pop(expired_id, None)
        threading.Thread(target=self._execute, args=(job_id,), name=f"bonsai-run-{job_id[:8]}", daemon=True).start()
        return self.get(job_id)

    def get(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None and self.repository is not None:
                job = self.repository.get_job(job_id)
            if job is None:
                raise KeyError(job_id)
            public_job = {key: value for key, value in job.items() if key != "_trace"}
            return copy.deepcopy(public_job)

    def _persist(self, job: dict[str, Any]) -> None:
        if self.repository is not None:
            self.repository.save_job({key: value for key, value in job.items() if key != "_trace"})

    def _transition(self, job_id: str, next_state: str, details: dict[str, Any] | None = None) -> None:
        with self._lock:
            self._machines[job_id].transition(next_state)
            now = time.time()
            job = self._jobs[job_id]
            job["state"] = next_state
            job["updated_at"] = now
            event = {"state": next_state, "at": now}
            if details:
                event["details"] = details
            job["events"].append(event)
            trace = job.get("_trace")
            if trace is not None:
                trace.event(next_state, **(details or {}))
                if next_state == "awaiting_review":
                    trace.finish("ok", **(details or {}))
                elif next_state == "failed":
                    trace.finish("error", error=job.get("error", {}).get("message"), **(details or {}))
            self._persist(job)

    def _execute(self, job_id: str) -> None:
        with self._capacity:
            job = self.get(job_id)
            try:
                service = self.service_factory()

                def observe(stage: str, details: dict[str, Any] | None = None) -> None:
                    self._transition(job_id, stage, details)

                run = service.run(job["question"], job["corpus"], job["case_id"], observer=observe)
                with self._lock:
                    self._jobs[job_id]["run"] = run
                    self._persist(self._jobs[job_id])
                self._transition(job_id, "awaiting_review", {"run_id": run["id"]})
            except Exception as error:
                with self._lock:
                    current = self._jobs[job_id]["state"]
                    self._jobs[job_id]["failed_stage"] = current
                    self._jobs[job_id]["error"] = {"kind": type(error).__name__, "message": str(error), "retryable": True}
                    self._persist(self._jobs[job_id])
                if current not in {"failed", "awaiting_review"}:
                    self._transition(job_id, "failed", {"failed_stage": current, "error_kind": type(error).__name__})
