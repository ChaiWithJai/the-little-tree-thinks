from __future__ import annotations

from typing import Any


class BonsaiAgentAdapter:
    """Narrow adapter around the existing local retrieval and model module."""

    def __init__(self, agent: Any):
        self.agent = agent

    @property
    def model_id(self) -> str:
        return self.agent.config()["lm_studio"]["chat_model"]

    def search(self, question: str, limit: int, corpus: str | None) -> list[dict]:
        return self.agent.search(question, limit, corpus)

    def synthesize(self, question: str, hits: list[dict]) -> tuple[str | None, str | None]:
        return self.agent.synthesize(question, hits)
