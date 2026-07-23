from __future__ import annotations

import re
import time
import uuid
from collections.abc import Callable
from typing import Protocol

from .domain import SCHEMA_VERSION, validate_corpus, validate_review


class RagAdapter(Protocol):
    @property
    def model_id(self) -> str: ...
    def search(self, question: str, limit: int, corpus: str | None) -> list[dict]: ...
    def synthesize(self, question: str, hits: list[dict]) -> tuple[str | None, str | None]: ...


class RunRepository(Protocol):
    def save(self, run: dict) -> None: ...
    def recent(self, limit: int) -> list[dict]: ...
    def update_review(self, run_id: str, review: dict) -> dict | None: ...


class EvaluationService:
    def __init__(self, rag: RagAdapter, repository: RunRepository, *, retrieval_limit: int, history_limit: int, allowed_issues: set[str]):
        self.rag = rag
        self.repository = repository
        self.retrieval_limit = retrieval_limit
        self.history_limit = history_limit
        self.allowed_issues = allowed_issues

    def run(
        self,
        question: str,
        corpus: str | None,
        case_id: str | None = None,
        *,
        observer: Callable[[str, dict | None], None] | None = None,
    ) -> dict:
        question = str(question).strip()
        if not question:
            raise ValueError("A case question is required.")
        corpus = validate_corpus(corpus)
        started = time.perf_counter()
        if observer:
            observer("retrieving", None)
        hits = self.rag.search(question, self.retrieval_limit, corpus)
        if observer and hits:
            observer("synthesizing", {"retrieved_sources": len(hits)})
        answer, error = self.rag.synthesize(question, hits) if hits else (None, "No relevant local sources found.")
        if observer:
            observer("validating", {"retrieved_sources": len(hits)})
        citations = sorted({int(value) for value in re.findall(r"\[S(\d+)\]", answer or "")})
        run = {
            "schema_version": SCHEMA_VERSION,
            "id": uuid.uuid4().hex,
            "case_id": case_id,
            "created_at": time.time(),
            "question": question,
            "corpus": corpus,
            "answer": answer,
            "error": error,
            "mode": "model" if answer else "retrieval-fallback",
            "model": self.rag.model_id,
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "hits": hits,
            "checks": {
                "has_answer": bool(answer),
                "has_citations": bool(citations),
                "citations_resolve": bool(citations) and all(1 <= value <= len(hits) for value in citations),
                "retrieved_sources": len(hits),
            },
            "review": None,
        }
        if observer:
            observer("checkpointing", {"citations_resolve": run["checks"]["citations_resolve"]})
        self.repository.save(run)
        return run

    def recent(self) -> list[dict]:
        return self.repository.recent(self.history_limit)

    def review(self, run_id: str, verdict: object, issues: object, note: object) -> dict | None:
        review = validate_review(verdict, issues, note, self.allowed_issues)
        review["reviewed_at"] = time.time()
        return self.repository.update_review(str(run_id), review)
