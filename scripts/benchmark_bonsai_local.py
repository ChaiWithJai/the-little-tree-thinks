#!/usr/bin/env python3
"""Run repeatable local HTML/image cases and export their durable trace summary."""
from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.request
from pathlib import Path
from typing import Any


def request_json(base: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(
        base.rstrip("/") + path, data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method="POST" if data else "GET",
    )
    with urllib.request.urlopen(request, timeout=240) as response:
        return json.load(response)


def wait_for_job(base: str, job_id: str) -> dict[str, Any]:
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        job = request_json(base, f"/api/jobs/{job_id}")["job"]
        if job["state"] in {"awaiting_review", "failed"}:
            return job
        time.sleep(.4)
    raise TimeoutError(f"Job {job_id} did not finish within 240 seconds")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--html", type=int, default=0, help="Run the first N page presets (0 only reports existing traces).")
    parser.add_argument("--image", type=int, default=0, help="Run N fixed-seed Bonsai image renders.")
    parser.add_argument("--output", type=Path, default=Path("output/benchmarks/bonsai-local.json"))
    args = parser.parse_args()
    started = time.time()
    results: list[dict[str, Any]] = []
    if args.html:
        presets = request_json(args.base_url, "/api/page-presets")["presets"][:args.html]
        for preset in presets:
            prompt = preset["prompt"] + "\n\nAcceptance criteria:\n" + "\n".join(f"- {item}" for item in preset["acceptance"])
            created = request_json(args.base_url, "/api/jobs", {"mode": "html", "case_id": preset["id"], "question": prompt, "corpus": None})
            job = wait_for_job(args.base_url, created["job"]["id"])
            run = job.get("run") or {}
            results.append({
                "kind": "html", "case_id": preset["id"], "state": job["state"], "trace_id": job.get("trace_id"),
                "latency_ms": run.get("latency_ms"), "quality_score": run.get("quality", {}).get("score"),
                "recovered": run.get("generation", {}).get("recovered"), "artifact": run.get("artifact", {}).get("url"),
                "error": job.get("error"),
            })
    for index in range(args.image):
        prompt = "Editorial menswear material study, linen, denim and tobacco leather, warm cream paper, cinematic still"
        before = time.perf_counter()
        try:
            image = request_json(args.base_url, "/api/image", {"prompt": prompt, "seed": 2407 + index, "steps": 2, "size": "512x512"})
            results.append({"kind": "image", "state": "ok", "trace_id": image.get("trace_id"), "latency_ms": round((time.perf_counter() - before) * 1000), "artifact": image.get("url")})
        except Exception as error:
            results.append({"kind": "image", "state": "failed", "latency_ms": round((time.perf_counter() - before) * 1000), "error": str(error)})
    report = {
        "schema_version": 1, "started_at": started, "base_url": args.base_url, "results": results,
        "trace_summary": request_json(args.base_url, "/api/benchmarks/summary?limit=500"),
    }
    latencies = [item["latency_ms"] for item in results if isinstance(item.get("latency_ms"), (int, float))]
    qualities = [item["quality_score"] for item in results if isinstance(item.get("quality_score"), (int, float))]
    report["run_summary"] = {
        "count": len(results), "successes": sum(item["state"] in {"ok", "awaiting_review"} for item in results),
        "latency_median_ms": round(statistics.median(latencies)) if latencies else None,
        "quality_mean": round(statistics.mean(qualities), 1) if qualities else None,
        "recovered": sum(bool(item.get("recovered")) for item in results),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
