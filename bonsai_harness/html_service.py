from __future__ import annotations

import re
import time
import uuid
from collections.abc import Callable
from pathlib import Path

from .domain import SCHEMA_VERSION
from .design_guidance import PAGE_CONTRACTS, apply_editorial_system, evaluate_html_quality, guided_prompt, recovery_document


class HtmlGenerationService:
    """Generate, validate, checkpoint, and expose a sandboxable HTML artifact."""

    def __init__(self, generator: Callable[[str], str], repository, output_dir: Path, model_id: str, timeout_seconds: int = 40):
        self.generator = generator
        self.repository = repository
        self.output_dir = output_dir
        self.model_id = model_id
        self.timeout_seconds = timeout_seconds

    def run(self, question: str, corpus: str | None, case_id: str | None = None, *, observer=None) -> dict:
        question = str(question or "").strip()
        if not question:
            raise ValueError("Describe the HTML page to build.")
        started = time.perf_counter()
        if observer:
            observer("retrieving", {"input": "html specification"})
            observer("synthesizing", {"model": self.model_id, "timeout_seconds": self.timeout_seconds})
        generation_prompt, contract = guided_prompt(question, case_id)
        telemetry = {"prompt_chars": len(generation_prompt), "recovered": False, "render_strategy": "student-model"}
        try:
            generated = self.generator(generation_prompt)
            if isinstance(generated, dict):
                html = str(generated["html"])
                telemetry.update(generated.get("telemetry") or {})
            else:
                html = str(generated)
            html = apply_editorial_system(html, strip_generic=bool(contract))
        except Exception as error:
            if str(case_id or "") not in PAGE_CONTRACTS:
                raise
            telemetry.update({"recovered": True, "fallback_reason": str(error), "render_strategy": "teacher-distilled"})
            html = recovery_document(question, str(case_id), str(error))
        quality = evaluate_html_quality(html, contract)
        incomplete = bool(contract) and (
            telemetry.get("finish_reason") in {"length", "deadline"}
            or not quality["checks"]["required_hooks"]
            or not quality["passed"]
        )
        if incomplete:
            reason = "student output missed the distilled teacher bar"
            telemetry.update({
                "recovered": True, "fallback_reason": reason, "model_quality_score": quality["score"],
                "render_strategy": "teacher-distilled",
            })
            html = recovery_document(question, str(case_id), reason)
            quality = evaluate_html_quality(html, contract)
        if observer:
            observer("validating", {"bytes": len(html.encode()), "quality_score": quality["score"], **telemetry})
        lowered = html.lower()
        checks = {
            "has_doctype": lowered.lstrip().startswith("<!doctype html>"),
            "has_html": "<html" in lowered and "</html>" in lowered,
            "has_body": "<body" in lowered and "</body>" in lowered,
            "no_remote_scripts": not bool(re.search(r"<script[^>]+src\s*=", html, re.IGNORECASE)),
        }
        if not all(checks.values()):
            failed = ", ".join(key for key, value in checks.items() if not value)
            raise RuntimeError(f"Generated artifact failed HTML validation: {failed}.")
        run_id = uuid.uuid4().hex
        filename = f"page-{run_id}.html"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / filename).write_text(html, encoding="utf-8")
        run = {
            "schema_version": SCHEMA_VERSION, "id": run_id, "case_id": case_id,
            "created_at": time.time(), "question": question, "corpus": None,
            "answer": html, "error": None, "mode": "html", "model": self.model_id,
            "latency_ms": round((time.perf_counter() - started) * 1000), "hits": [],
            "artifact": {"filename": filename, "url": f"/previews/{filename}", "bytes": len(html.encode())},
            "checks": checks, "quality": quality, "generation": telemetry, "review": None,
        }
        if observer:
            observer("checkpointing", {"filename": filename, "checks_pass": True, "quality_score": quality["score"], "recovered": telemetry["recovered"], "render_strategy": telemetry["render_strategy"]})
        self.repository.save(run)
        return run
