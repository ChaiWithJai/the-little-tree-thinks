from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from contextlib import closing
from pathlib import Path
from typing import Any


class LocalTraceStore:
    """Small, dependency-free trace store for local model benchmarks."""

    def __init__(self, database_path: Path):
        self.database_path = database_path
        self._lock = threading.RLock()
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS traces (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at REAL NOT NULL,
                    ended_at REAL,
                    duration_ms INTEGER,
                    job_id TEXT,
                    case_id TEXT,
                    model TEXT,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS traces_started_at_idx ON traces(started_at DESC);
                CREATE INDEX IF NOT EXISTS traces_kind_idx ON traces(kind, started_at DESC);
                CREATE INDEX IF NOT EXISTS traces_job_id_idx ON traces(job_id);
                """
            )

    def _connection(self):
        store = self

        class ConnectionContext:
            def __enter__(self):
                self.connection = sqlite3.connect(store.database_path, timeout=10)
                self.connection.row_factory = sqlite3.Row
                self.connection.execute("PRAGMA journal_mode=WAL")
                return self.connection

            def __exit__(self, exception_type, exception, traceback):
                if exception is None:
                    self.connection.commit()
                else:
                    self.connection.rollback()
                self.connection.close()

        return ConnectionContext()

    def start(self, kind: str, name: str, **attributes: Any) -> "LocalTrace":
        now = time.time()
        payload = {
            "id": uuid.uuid4().hex,
            "kind": kind,
            "name": name,
            "status": "running",
            "started_at": now,
            "ended_at": None,
            "duration_ms": None,
            "attributes": attributes,
            "events": [{"name": "trace.started", "at": now, "attributes": {}}],
            "error": None,
        }
        self._save(payload)
        return LocalTrace(self, payload)

    def _save(self, payload: dict[str, Any]) -> None:
        attributes = payload.get("attributes", {})
        with self._lock, self._connection() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO traces
                   (id, kind, name, status, started_at, ended_at, duration_ms, job_id, case_id, model, payload_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    payload["id"], payload["kind"], payload["name"], payload["status"], payload["started_at"],
                    payload.get("ended_at"), payload.get("duration_ms"), attributes.get("job_id"),
                    attributes.get("case_id"), attributes.get("model"), json.dumps(payload, ensure_ascii=False),
                ),
            )

    def recent(self, limit: int = 50, kind: str | None = None) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 500))
        with self._connection() as connection:
            if kind:
                rows = connection.execute(
                    "SELECT payload_json FROM traces WHERE kind=? ORDER BY started_at DESC LIMIT ?", (kind, limit)
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT payload_json FROM traces ORDER BY started_at DESC LIMIT ?", (limit,)
                ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def summary(self, limit: int = 200) -> dict[str, Any]:
        traces = [item for item in self.recent(limit) if item.get("status") != "running"]
        groups: dict[str, list[dict[str, Any]]] = {}
        for trace in traces:
            groups.setdefault(trace["kind"], []).append(trace)
        output: dict[str, Any] = {"sample_size": len(traces), "by_kind": {}}
        for kind, items in groups.items():
            durations = sorted(int(item.get("duration_ms") or 0) for item in items)
            quality = [item.get("attributes", {}).get("quality_score") for item in items]
            quality = [float(value) for value in quality if isinstance(value, (int, float))]
            stage_samples: dict[str, list[int]] = {}
            for item in items:
                events = item.get("events", [])
                for current, following in zip(events, events[1:]):
                    name = current.get("name")
                    if name == "trace.started":
                        continue
                    duration = max(0, round((following.get("at", 0) - current.get("at", 0)) * 1000))
                    stage_samples.setdefault(name, []).append(duration)
            stages = {}
            for name, values in stage_samples.items():
                values.sort()
                stages[name] = {
                    "count": len(values),
                    "p50_ms": values[(len(values) - 1) // 2],
                    "p95_ms": values[min(len(values) - 1, int(len(values) * .95))],
                }
            output["by_kind"][kind] = {
                "count": len(items),
                "success_rate": round(sum(item["status"] == "ok" for item in items) / len(items), 3),
                "p50_ms": durations[(len(durations) - 1) // 2],
                "p95_ms": durations[min(len(durations) - 1, int(len(durations) * .95))],
                "quality_mean": round(sum(quality) / len(quality), 1) if quality else None,
                "stages": stages,
            }
        return output


class LocalTrace:
    def __init__(self, store: LocalTraceStore, payload: dict[str, Any]):
        self.store = store
        self.payload = payload

    @property
    def id(self) -> str:
        return self.payload["id"]

    def event(self, name: str, **attributes: Any) -> None:
        self.payload["events"].append({"name": name, "at": time.time(), "attributes": attributes})
        self.payload["attributes"].update({key: value for key, value in attributes.items() if key in {
            "model", "first_token_ms", "output_chars", "quality_score", "bounded", "finish_reason"
        }})
        self.store._save(self.payload)

    def finish(self, status: str = "ok", error: str | None = None, **attributes: Any) -> None:
        ended = time.time()
        self.payload.update({
            "status": status,
            "ended_at": ended,
            "duration_ms": round((ended - self.payload["started_at"]) * 1000),
            "error": error,
        })
        self.payload["attributes"].update(attributes)
        self.payload["events"].append({"name": "trace.finished", "at": ended, "attributes": {"status": status}})
        self.store._save(self.payload)
