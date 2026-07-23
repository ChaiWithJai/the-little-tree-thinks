#!/usr/bin/env python3
"""Validate the portable creative-harness evaluation package."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVALUATION = ROOT / "docs" / "evaluation"

REQUIRED_FILES = [
    "README.md",
    "PROOF.md",
    "scorecard.json",
    "RFC-0002-CREATIVE-ARTIFACT-GRAPH.md",
    "ARCHITECTURE-REVIEW.md",
    "DESIGN-TREATMENTS.md",
    "ISSUE.md",
    "PRIOR-ART.md",
    "SOURCE-MANIFEST.md",
    "sol-5-6-target.html",
    "assets/bonsai-journey-arrival.png",
    "assets/bonsai-storyboard-run.png",
    "assets/bonsai-storyboard-artifact.png",
    "assets/sol-5-6-target-contract.png",
    "assets/sol-5-6-target-mobile.png",
    "assets/provider-delta-openai-left-bonsai-right.png",
    "assets/target-airplane-mode-storyboard.png",
    "assets/target-margin-test-storyboard.png",
    "assets/target-new-tenant-storyboard.png",
    "assets/airplane-mode-provider-delta.jpg",
    "assets/margin-test-provider-delta.jpg",
    "assets/new-tenant-provider-delta.jpg",
]

PROOF_HASHES = {
    "assets/bonsai-storyboard-run.png":
        "a37eccefc720a142c7b9e67f813f8303058d3f52a8ea7cab9a25f921fcaab84a",
    "assets/sol-5-6-target-contract.png":
        "1ff589278ebea6a732df7bcf07407041472eb151244569004681b91b97d50841",
    "assets/provider-delta-openai-left-bonsai-right.png":
        "79ebea770c968cc3332091acf411c3c00533746117f6120afda2052218bfc42e",
    "scorecard.json":
        "b0cef2385935c29ac97b7b67f6d37428026c5e91a791ef21642d06a2d86d200f",
}


def main() -> None:
    missing = [name for name in REQUIRED_FILES if not (EVALUATION / name).is_file()]
    if missing:
        raise SystemExit(f"Missing evaluation files: {', '.join(missing)}")

    scorecard = json.loads((EVALUATION / "scorecard.json").read_text())
    assert scorecard["comparisonPolicy"]["targetEvidence"] == "inferred"
    assert scorecard["workbench"]["jobs"] == (
        scorecard["workbench"]["reviewable"] + scorecard["workbench"]["failed"]
    )
    assert scorecard["production"]["renderedFramesPerFilm"] == (
        scorecard["production"]["durationSecondsPerFilm"]
        * scorecard["production"]["fps"]
    )
    assert scorecard["production"]["totalRenderedFrames"] == (
        scorecard["production"]["films"]
        * scorecard["production"]["renderedFramesPerFilm"]
    )
    assert scorecard["production"]["totalStills"] == (
        scorecard["production"]["films"] * scorecard["production"]["stillsPerFilm"]
    )
    assert scorecard["production"]["validationPassed"] is True
    assert scorecard["production"]["forcedAlignment"] is False

    for dimension in scorecard["rubric"]["dimensions"]:
        assert 0 <= dimension["current"] <= 5
        assert 0 <= dimension["target"] <= 5
        assert dimension["evidence"]

    for name, expected in PROOF_HASHES.items():
        actual = hashlib.sha256((EVALUATION / name).read_bytes()).hexdigest()
        assert actual == expected, f"Proof hash mismatch for {name}"

    print(
        "Creative evaluation valid:",
        len(REQUIRED_FILES),
        "files,",
        len(scorecard["rubric"]["dimensions"]),
        "rubric dimensions,",
        len(PROOF_HASHES),
        "proof hashes",
    )


if __name__ == "__main__":
    main()
