from __future__ import annotations

from dataclasses import dataclass


class InvalidTransition(ValueError):
    pass


RUN_TRANSITIONS: dict[str, set[str]] = {
    "queued": {"retrieving", "failed"},
    "retrieving": {"synthesizing", "validating", "failed"},
    "synthesizing": {"validating", "failed"},
    "validating": {"checkpointing", "failed"},
    "checkpointing": {"awaiting_review", "failed"},
    "awaiting_review": set(),
    "failed": set(),
}


@dataclass
class RunStateMachine:
    state: str = "queued"

    def transition(self, next_state: str) -> str:
        allowed = RUN_TRANSITIONS.get(self.state)
        if allowed is None or next_state not in allowed:
            raise InvalidTransition(f"Illegal run transition: {self.state} -> {next_state}")
        self.state = next_state
        return self.state
