from __future__ import annotations

import json
from pathlib import Path

from .domain import EvalCase, ReviewIssue, SCHEMA_VERSION


class CaseCatalog:
    """Validated, file-backed evaluation policy and case catalog."""

    def __init__(self, path: Path):
        self.path = path

    def load(self) -> dict:
        try:
            raw = json.loads(self.path.read_text())
        except FileNotFoundError as error:
            raise RuntimeError(f"Case catalog not found: {self.path}") from error
        except json.JSONDecodeError as error:
            raise RuntimeError(f"Invalid case catalog JSON: {error}") from error
        if raw.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(f"Unsupported case catalog schema: {raw.get('schema_version')!r}.")
        cases = [EvalCase.from_mapping(item) for item in raw.get("cases", [])]
        issues = [ReviewIssue.from_mapping(item) for item in raw.get("review_issues", [])]
        _unique("case", [item.id for item in cases])
        _unique("review issue", [item.id for item in issues])
        if not cases:
            raise ValueError("The case catalog must contain at least one case.")
        return {"schema_version": SCHEMA_VERSION, "cases": [item.to_dict() for item in cases], "review_issues": [item.to_dict() for item in issues]}


def _unique(kind: str, values: list[str]) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {kind} ID in catalog.")
