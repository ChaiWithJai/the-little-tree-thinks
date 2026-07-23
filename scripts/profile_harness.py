#!/usr/bin/env python3
"""Read-only workload profiler for the local Bonsai harness."""
from __future__ import annotations

import argparse
import json
import platform
import sqlite3
import statistics
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import bonsai_agent as agent


def distribution(samples: list[float]) -> dict[str, float]:
    ordered = sorted(samples)
    percentile = lambda value: ordered[min(len(ordered) - 1, max(0, round((len(ordered) - 1) * value)))]
    return {"min": round(ordered[0], 3), "p50": round(statistics.median(ordered), 3), "p95": round(percentile(0.95), 3), "max": round(ordered[-1], 3)}


def fetch(url: str) -> float:
    started = time.perf_counter()
    with urllib.request.urlopen(url, timeout=10) as response:
        if response.status != 200:
            raise RuntimeError(f"{url} returned {response.status}")
        response.read()
    return (time.perf_counter() - started) * 1000


def profile_api(base_url: str, requests: int, concurrency: int) -> dict:
    paths = ["/api/cases", "/api/runs"]
    samples, errors = [], []
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(fetch, base_url.rstrip("/") + paths[index % len(paths)]) for index in range(requests)]
        for future in as_completed(futures):
            try:
                samples.append(future.result())
            except Exception as error:
                errors.append(str(error))
    elapsed = time.perf_counter() - started
    return {
        "requests": requests, "concurrency": concurrency, "errors": len(errors),
        "throughput_rps": round(len(samples) / elapsed, 2),
        "latency_ms": distribution(samples) if samples else None,
        "error_samples": errors[:3],
    }


def profile_retrieval(iterations: int) -> dict:
    cases = [
        ("dharma", "What does the workshop method say about motivation and opportunity?"),
        ("civic", "What makes the civic project inspectable and trustworthy?"),
        (None, "What operating principles appear across the Dharma and civic-tech projects?"),
    ]
    samples = []
    for _ in range(iterations):
        for corpus, question in cases:
            started = time.perf_counter()
            agent.search(question, 6, corpus)
            samples.append((time.perf_counter() - started) * 1000)
    index = agent.load_index()
    return {"queries": len(samples), "chunks": len(index["documents"]), "latency_ms": distribution(samples)}


def retained_runs() -> dict:
    database = agent.STATE_DIR / "evaluations" / "runs.sqlite3"
    if not database.exists():
        return {"count": 0, "text_latency_ms": []}
    with sqlite3.connect(database) as connection:
        runs = [json.loads(row[0]) for row in connection.execute("SELECT payload_json FROM runs")]
    latencies = [run["latency_ms"] for run in runs if run.get("latency_ms") is not None]
    return {"count": len(runs), "database_bytes": database.stat().st_size, "text_latency_ms": latencies, "fallbacks": sum(run.get("mode") != "model" for run in runs)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8765")
    parser.add_argument("--api-requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--retrieval-iterations", type=int, default=40)
    args = parser.parse_args()
    print(json.dumps({
        "captured_at": time.time(),
        "host": {"platform": platform.platform(), "processor": platform.processor()},
        "api": profile_api(args.base_url, args.api_requests, args.concurrency),
        "retrieval": profile_retrieval(args.retrieval_iterations),
        "retained_runs": retained_runs(),
        "state_bytes": sum(path.stat().st_size for path in agent.STATE_DIR.rglob("*") if path.is_file()),
    }, indent=2))


if __name__ == "__main__":
    main()
