#!/usr/bin/env python3
"""Export reviewed and teacher-rendered HTML runs as a local distillation dataset."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bonsai_harness.config import HarnessSettings
from bonsai_harness.design_guidance import guided_prompt, load_distillation
from bonsai_harness.repository import SQLiteRunRepository


def distillation_record(run: dict[str, Any], minimum_score: int) -> dict[str, Any] | None:
    if run.get("mode") != "html" or not run.get("answer"):
        return None
    quality_score = int((run.get("quality") or {}).get("score") or 0)
    review = run.get("review") or {}
    strategy = (run.get("generation") or {}).get("render_strategy")
    human_pass = review.get("verdict") == "pass"
    synthetic_teacher = strategy == "teacher-distilled" and quality_score >= minimum_score
    if not human_pass and not synthetic_teacher:
        return None
    guided, contract = guided_prompt(run.get("question", ""), run.get("case_id"))
    return {
        "schema_version": 1,
        "id": run["id"],
        "supervision": "human" if human_pass else "synthetic-teacher",
        "accepted": True,
        "case_id": run.get("case_id"),
        "messages": [
            {"role": "system", "content": "Produce one finished, self-contained HTML document that follows the supplied distilled design program."},
            {"role": "user", "content": guided},
            {"role": "assistant", "content": run["answer"]},
        ],
        "metadata": {
            "quality_score": quality_score,
            "distillation_version": (run.get("quality") or {}).get("distillation_version"),
            "render_strategy": strategy,
            "review": review or None,
            "contract": contract,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/distillation/html-teacher.jsonl"))
    parser.add_argument("--minimum-score", type=int, default=88)
    parser.add_argument("--limit", type=int, default=5000)
    args = parser.parse_args()
    settings = HarnessSettings.from_env(ROOT)
    repository = SQLiteRunRepository(settings.database_path, settings.legacy_runs_path)
    records = [record for run in repository.recent(args.limit) if (record := distillation_record(run, args.minimum_score))]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records))
    summary = {
        "output": str(args.output.resolve()), "records": len(records),
        "human": sum(record["supervision"] == "human" for record in records),
        "synthetic_teacher": sum(record["supervision"] == "synthetic-teacher" for record in records),
        "distillation_version": load_distillation()["version"],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
