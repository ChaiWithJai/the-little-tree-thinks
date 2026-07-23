from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

SCHEMA_VERSION = 1
VERDICTS = {"pass", "needs-work", "fail"}


@dataclass(frozen=True)
class EvalCase:
    id: str
    title: str
    question: str
    corpus: str | None
    intent: str
    benchmark: str | None = None
    category: str | None = None
    acceptance: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EvalCase":
        case = cls(
            id=_required_text(value, "id"),
            title=_required_text(value, "title"),
            question=_required_text(value, "question"),
            corpus=value.get("corpus"),
            intent=_required_text(value, "intent"),
            benchmark=str(value.get("benchmark") or "").strip() or None,
            category=str(value.get("category") or "").strip() or None,
            acceptance=tuple(str(item).strip() for item in value.get("acceptance", []) if str(item).strip()),
        )
        validate_corpus(case.corpus)
        return case

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "title": self.title, "question": self.question,
            "corpus": self.corpus, "intent": self.intent,
            "benchmark": self.benchmark, "category": self.category,
            "acceptance": list(self.acceptance),
        }


@dataclass(frozen=True)
class ReviewIssue:
    id: str
    label: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ReviewIssue":
        return cls(id=_required_text(value, "id"), label=_required_text(value, "label"))

    def to_dict(self) -> dict[str, str]:
        return {"id": self.id, "label": self.label}


def validate_review(verdict: Any, issues: Any, note: Any, allowed_issues: set[str]) -> dict[str, Any]:
    if verdict not in VERDICTS:
        raise ValueError("Choose a valid verdict.")
    if not isinstance(issues, list) or not all(isinstance(issue, str) for issue in issues):
        raise ValueError("Review issues must be a list of issue IDs.")
    unknown = set(issues) - allowed_issues
    if unknown:
        raise ValueError(f"Unknown review issue: {sorted(unknown)[0]}.")
    return {"verdict": verdict, "issues": list(dict.fromkeys(issues)), "note": str(note or "").strip()}


def validate_corpus(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", value):
        raise ValueError("Corpus names must use lowercase letters, numbers, underscores, or hyphens.")
    return value


def _required_text(value: Mapping[str, Any], field: str) -> str:
    result = str(value.get(field, "")).strip()
    if not result:
        raise ValueError(f"{field} is required.")
    return result
