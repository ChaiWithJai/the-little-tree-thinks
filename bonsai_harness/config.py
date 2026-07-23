from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HarnessSettings:
    """Runtime configuration with environment overrides for deployment."""

    root: Path
    state_dir: Path
    database_path: Path
    legacy_runs_path: Path
    case_catalog_path: Path
    host: str = "127.0.0.1"
    port: int = 8765
    history_limit: int = 30
    retrieval_limit: int = 6
    max_concurrent_runs: int = 1

    @classmethod
    def from_env(cls, root: Path) -> "HarnessSettings":
        root = root.resolve()
        state_dir = Path(os.getenv("BONSAI_STATE_DIR", root / ".bonsai-agent")).expanduser().resolve()

        def path_setting(name: str, default: Path) -> Path:
            return Path(os.getenv(name, default)).expanduser().resolve()

        return cls(
            root=root,
            state_dir=state_dir,
            database_path=path_setting("BONSAI_HARNESS_DB", state_dir / "evaluations" / "runs.sqlite3"),
            legacy_runs_path=path_setting("BONSAI_LEGACY_RUNS", state_dir / "evaluations" / "runs.json"),
            case_catalog_path=path_setting("BONSAI_CASES_PATH", root / "evals" / "cases.json"),
            host=os.getenv("BONSAI_HOST", "127.0.0.1"),
            port=_positive_int("BONSAI_PORT", 8765),
            history_limit=_positive_int("BONSAI_HISTORY_LIMIT", 30),
            retrieval_limit=_positive_int("BONSAI_RETRIEVAL_LIMIT", 6),
            max_concurrent_runs=_positive_int("BONSAI_MAX_CONCURRENT_RUNS", 1),
        )


def _positive_int(name: str, default: int) -> int:
    value = int(os.getenv(name, default))
    if value < 1:
        raise ValueError(f"{name} must be positive.")
    return value
