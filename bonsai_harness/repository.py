from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class SQLiteRunRepository:
    """Transactional run storage with an idempotent legacy JSON import."""

    def __init__(self, database_path: Path, legacy_path: Path | None = None):
        self.database_path = database_path
        self.legacy_path = legacy_path
        self._lock = threading.RLock()
        database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _open(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @contextmanager
    def _connect(self):
        connection = self._open()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._lock, self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    created_at REAL NOT NULL,
                    case_id TEXT,
                    corpus TEXT,
                    verdict TEXT,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS runs_created_at_idx ON runs(created_at DESC);
                CREATE INDEX IF NOT EXISTS runs_case_id_idx ON runs(case_id);
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    state TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS jobs_updated_at_idx ON jobs(updated_at DESC);
                PRAGMA user_version=2;
                """
            )
            imported = connection.execute("SELECT value FROM metadata WHERE key='legacy_runs_imported'").fetchone()
            if imported is None:
                for run in self._read_legacy():
                    self._insert(connection, run, replace=False)
                connection.execute("INSERT INTO metadata(key, value) VALUES('legacy_runs_imported', '1')")

    def _read_legacy(self) -> list[dict[str, Any]]:
        if not self.legacy_path or not self.legacy_path.exists():
            return []
        try:
            value = json.loads(self.legacy_path.read_text())
        except (OSError, json.JSONDecodeError):
            return []
        return [item for item in value if isinstance(item, dict) and item.get("id")] if isinstance(value, list) else []

    @staticmethod
    def _insert(connection: sqlite3.Connection, run: dict[str, Any], *, replace: bool) -> None:
        verb = "INSERT OR REPLACE" if replace else "INSERT OR IGNORE"
        review = run.get("review") or {}
        connection.execute(
            f"{verb} INTO runs(id, created_at, case_id, corpus, verdict, payload_json) VALUES(?, ?, ?, ?, ?, ?)",
            (run["id"], float(run.get("created_at", 0)), run.get("case_id"), run.get("corpus"), review.get("verdict"), json.dumps(run, ensure_ascii=False)),
        )

    def save(self, run: dict[str, Any]) -> None:
        with self._lock, self._connect() as connection:
            self._insert(connection, run, replace=False)

    def recent(self, limit: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT payload_json FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def get(self, run_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT payload_json FROM runs WHERE id=?", (run_id,)).fetchone()
        return json.loads(row["payload_json"]) if row else None

    def update_review(self, run_id: str, review: dict[str, Any]) -> dict[str, Any] | None:
        with self._lock, self._connect() as connection:
            row = connection.execute("SELECT payload_json FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                return None
            run = json.loads(row["payload_json"])
            run["review"] = review
            self._insert(connection, run, replace=True)
            return run

    def save_job(self, job: dict[str, Any]) -> None:
        """Persist the latest job snapshot so browser polling survives restarts."""
        with self._lock, self._connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO jobs(id, created_at, updated_at, state, payload_json)
                   VALUES(?, ?, ?, ?, ?)""",
                (job["id"], float(job["created_at"]), float(job["updated_at"]), job["state"], json.dumps(job, ensure_ascii=False)),
            )

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT payload_json FROM jobs WHERE id=?", (job_id,)).fetchone()
        return json.loads(row["payload_json"]) if row else None

    def recover_interrupted_jobs(self, *, retained: int = 100) -> list[dict[str, Any]]:
        """Turn jobs abandoned by a process exit into explicit retryable failures."""
        import time

        terminal = {"awaiting_review", "failed"}
        recovered: list[dict[str, Any]] = []
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM jobs ORDER BY updated_at DESC LIMIT ?", (retained,)
            ).fetchall()
            for row in rows:
                job = json.loads(row["payload_json"])
                if job.get("state") not in terminal:
                    now = time.time()
                    failed_stage = job.get("state") or "queued"
                    job.update({
                        "state": "failed",
                        "updated_at": now,
                        "failed_stage": failed_stage,
                        "error": {
                            "kind": "ProcessRestart",
                            "message": "The local server restarted before this run completed. Retry to start a clean run.",
                            "retryable": True,
                        },
                    })
                    job.setdefault("events", []).append({
                        "state": "failed", "at": now, "details": {"failed_stage": failed_stage, "recovered_after_restart": True}
                    })
                    connection.execute(
                        "UPDATE jobs SET updated_at=?, state='failed', payload_json=? WHERE id=?",
                        (now, json.dumps(job, ensure_ascii=False), job["id"]),
                    )
                recovered.append(job)
        return list(reversed(recovered))
