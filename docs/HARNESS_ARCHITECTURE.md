# Evaluation harness architecture

This document describes the current prototype. The independent review in
`docs/evaluation/ARCHITECTURE-REVIEW.md` identifies the storage and execution
changes required before the storyboard to film journey.

The harness is organized around replaceable boundaries rather than HTTP handlers:

```text
evals/cases.json → CaseCatalog ───────────────┐
                                               ↓
BonsaiAgentAdapter → EvaluationService → SQLiteRunRepository
                             ↑                 ↓
                        thin HTTP API ← browser workbench
                             ↓
                       LocalTraceStore → benchmark JSON
```

## Responsibilities

- `evals/cases.json` owns evaluation cases and the human-review taxonomy.
- `bonsai_harness/domain.py` validates stable case and review contracts.
- `bonsai_harness/service.py` orchestrates retrieval, synthesis, checks, and review.
- `bonsai_harness/adapters.py` isolates the existing local Bonsai agent API.
- `bonsai_harness/repository.py` provides transactional SQLite persistence.
- `bonsai_harness/tracing.py` records local spans and aggregates benchmark latency,
  success, and quality metrics without a telemetry dependency.
- `bonsai_harness/design_guidance.py` compiles page-specific visual contracts, injects
  the shared editorial system, scores finished HTML, and supplies bounded recovery pages.
- `evals/html-distillation.json` is the versioned teacher program; it holds portable design
  lessons rather than burying taste in model weights or one opaque system prompt.
- `bonsai_agent_web.py` only translates HTTP requests and responses.

The repository imports `.bonsai-agent/evaluations/runs.json` exactly once and leaves the
legacy file untouched. New runs are written to `runs.sqlite3`; no retention cap silently
deletes evaluation history.

The trace table is append-oriented and lives in that database. The `/api/traces` endpoint
returns inspectable spans, while `/api/benchmarks/summary` computes p50/p95 latency,
success rate, and mean quality by workload kind. `scripts/benchmark_bonsai_local.py`
drives the public local API so its results cover the same queue, model, validation,
checkpoint, image-demo, and recovery paths used by the browser.

The HTML path is a teacher/student cascade. The small local model attempts the full page
with distilled guidance. Validation measures both technical correctness and art-direction
fidelity. A clipped or low-fidelity student artifact remains observable in telemetry, while
the deterministic teacher renderer produces the displayed result. Reviewed outputs can be
exported with `scripts/export_html_distillation.py` as local JSONL supervision for the next
teacher-program revision or an eventual student fine-tune.

## Configuration

The defaults remain local-only. Production-like process configuration is available
without editing source:

| Variable | Default |
| --- | --- |
| `BONSAI_HOST` | `127.0.0.1` |
| `BONSAI_PORT` | `8765` |
| `BONSAI_STATE_DIR` | `.bonsai-agent` |
| `BONSAI_HARNESS_DB` | `.bonsai-agent/evaluations/runs.sqlite3` |
| `BONSAI_LEGACY_RUNS` | `.bonsai-agent/evaluations/runs.json` |
| `BONSAI_CASES_PATH` | `evals/cases.json` |
| `BONSAI_HISTORY_LIMIT` | `30` |
| `BONSAI_RETRIEVAL_LIMIT` | `6` |

Run the contract suite with:

```bash
python3 -m unittest discover -s tests -v
```
