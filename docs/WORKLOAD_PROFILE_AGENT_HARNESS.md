# Workload profile and capacity plan: Bonsai agent harness

| Field | Value |
| --- | --- |
| Status | Baseline captured; scale tests planned |
| Captured | 2026-07-22 |
| Reference host | Apple M4 Pro, 12 cores, 24 GB unified memory, macOS 26.5 |
| Reproduction | `python3 scripts/profile_harness.py` |

## Canonical method

HashiCorp’s Well-Architected Framework defines a three-part capacity workflow: profile the workload with load and stress tests, design for scale using the resulting limits, then monitor and respond before thresholds are reached. It calls out CPU, memory, response latency, and application error rate as the core measurements. This plan uses that exact sequence. Reference: [Design and scale compute instances](https://developer.hashicorp.com/well-architected-framework/optimize-systems/select-design/compute).

HashiCorp’s Nomad resource model is also useful as vocabulary: distinguish typical reservation from hard maximum, declare device needs, and avoid raising limits without measuring utilization. We use those concepts for the local model allocations without claiming that the current harness runs on Nomad. Reference: [Nomad resources block](https://developer.hashicorp.com/nomad/docs/job-specification/resources).

## Workload decomposition

| Class | Shape | Current implementation | Constrained resource | Scheduling policy |
| --- | --- | --- | --- | --- |
| Control plane | Short-lived service requests | Static files, status, cases, runs, review | HTTP threads, SQLite reads | Concurrent |
| Retrieval | CPU/memory scan, ~50 ms | Lexical scoring over JSON index | CPU and index residency | Concurrent initially; measure contention |
| Text inference | Long, compute/memory-intensive batch | LM Studio 27B completion | Unified memory, GPU/Metal, model slot | FIFO, capacity 1 |
| Validation | Short deterministic CPU | Citation parsing and resolution | CPU | Inline after inference |
| Checkpoint/review | Small transactional writes | SQLite WAL | Disk latency/lock | Serialized by repository lock |
| Image inference | Long device-intensive batch subprocess | Bonsai Image 4B MLX | Unified memory, GPU/Metal | Separate experiment; do not overlap with text until measured |
| Index build | Burst CPU, memory, disk write | Corpus walk/chunk/index JSON | CPU, RAM, disk | Offline maintenance batch |

## Baseline results

The baseline is a directional profile, not yet a production SLO proof.

### Control plane

Test: 100 alternating `/api/cases` and `/api/runs` requests, concurrency 8.

| Metric | Result |
| --- | ---: |
| Errors | 0 |
| Throughput | 1,072 requests/s |
| Latency p50 | 3.88 ms |
| Latency p95 | 38.07 ms |
| Latency max | 65.28 ms |

### Retrieval

Test: 120 searches across the three canonical cases over 2,003 indexed chunks.

| Metric | Result |
| --- | ---: |
| Latency p50 | 40.02 ms |
| Latency p95 | 47.98 ms |
| Latency max | 58.43 ms |
| Index file | 5.0 MB |

### Text inference

Available retained samples are too few for a statistically meaningful percentile.

| Run | End-to-end latency |
| --- | ---: |
| 1 | 54.326 s |
| 2 | 44.491 s |
| 3 | 37.435 s |

Median of the three is 44.491 s; all returned model artifacts rather than retrieval fallback. The next baseline requires at least 30 runs.

### Persistence and state

| Metric | Result |
| --- | ---: |
| Retained runs | 3 |
| SQLite database | 76 KB |
| Total `.bonsai-agent` state | 6.49 MB |

## Interpretation

1. **Inference dominates latency.** Optimizing HTTP or SQLite cannot materially improve the 37–54 second run experience.
2. **Backpressure is required.** One explicit inference allocation is safer than concurrent model calls on 24 GB unified memory.
3. **State is an interaction primitive.** Queue and stage visibility make long inference understandable without pretending it is faster.
4. **Retrieval headroom is currently healthy.** Its p95 is under the 100 ms initial target, but the algorithm scans every document and will grow roughly with index size.
5. **Control-plane capacity is not a scale concern today.** The baseline is far above expected single-operator load.
6. **Image/text overlap is unknown.** Both use unified-memory acceleration; concurrent execution is prohibited until measured.

## Test plan

### Phase 1 — repeatable baseline

Run on an otherwise idle reference host:

```bash
python3 scripts/profile_harness.py \
  --api-requests 100 \
  --concurrency 8 \
  --retrieval-iterations 40
```

Capture:

- host model, core count, memory, OS;
- Git revision and model IDs;
- index chunks and bytes;
- API/request distribution and errors;
- retrieval distribution;
- retained inference latencies and failures;
- state/database bytes.

Gate: three consecutive profiles remain within 20% of the established p95 values with zero control-plane errors.

### Phase 2 — canonical inference load test

Submit the three benchmark cases in round-robin order for 30 total text jobs with `max_concurrent_runs=1`.

Measure per stage from FSM events:

- queue wait;
- retrieval;
- synthesis;
- validation;
- checkpoint;
- total latency;
- fallback and failure rate;
- process RSS/unified-memory pressure, CPU/GPU utilization, and thermal throttling.

Initial gates:

- 30/30 jobs reach `awaiting_review` or a classified terminal failure;
- no illegal transition or missing run at `awaiting_review`;
- text p95 under the provisional 90-second guardrail;
- failure rate below 5%;
- no swap-growth trend or host OOM;
- queue wait approximately equals prior job duration when capacity is one.

### Phase 3 — stress and failure tests

| Scenario | Injection | Expected behavior |
| --- | --- | --- |
| Queue burst | Submit 10 jobs at once | One runs; nine remain queued; control plane stays responsive. |
| Server restart while queued | Restart before capacity acquisition | UI reports interrupted/unreachable; completed sessions survive. |
| Server restart during synthesis | Restart LM/server | Failure is classified; no run is claimed checkpointed. |
| LM Studio unavailable | Stop local model endpoint | Adapter reports unavailable; job fails/falls back according to contract. |
| SQLite unavailable | Make test database unwritable | State fails at `checkpointing`; `awaiting_review` is never emitted. |
| Invalid citation | Fake model returns `[S99]` | Validation records `citations_resolve=false`; artifact remains reviewable. |
| Retrieval miss | Query absent terms | `retrieving -> validating` is legal; no fabricated synthesis stage. |
| Browser poll interruption | Stop server after job acceptance | Browser shows `unreachable`, not model blocked. |
| Text plus image overlap | Run both under instrumentation | Do not enable by default until memory/latency gates pass. |

### Phase 4 — scale decision

Only after phases 1–3:

- Prefer **vertical tuning** for a single memory-intensive model allocation: model quantization, context/output bounds, and host memory headroom.
- Use **horizontal separation** when simultaneous text/image work or multiple operators becomes a requirement: one worker per device allocation and a shared durable queue.
- Do not raise local concurrency merely because the control plane has throughput headroom.

## Resource envelope to validate

The values below are test hypotheses, not reservations yet.

| Allocation | Typical reservation to measure | Hard condition |
| --- | --- | --- |
| Web/control | 1 CPU-equivalent, 256 MB excluding shared index | Must remain responsive during inference. |
| Retrieval/index | Index bytes plus Python object expansion; current profiler peak showed ~1.25 GB in a fresh process | Stop index growth test if host begins sustained swap. |
| Text model | One device slot; actual LM Studio memory must be sampled | No concurrent slot until p95 and memory gate pass. |
| Image model | One device slot, separate from text by default | Offline-only; terminate on configured timeout. |
| SQLite/state | Current state under 7 MB | Alert on unexpected unbounded growth or write failure. |

Nomad’s distinction between a typical memory reservation and a hard maximum is the intended model for a future scheduler: reserve for normal work, cap to prevent one allocation from destabilizing the host, and monitor OOM/throttling metrics. HashiCorp’s metrics reference includes allocation CPU, RSS/usage, OOM, restart, and pending/running counts; the harness should expose analogous job metrics. Reference: [Nomad metrics](https://developer.hashicorp.com/nomad/docs/reference/metrics).

## Instrumentation backlog

1. Persist job transition timestamps and run linkage in SQLite.
2. Add queue-depth, active-job, completion, failure, and duration counters.
3. Sample process/model RSS, CPU, and device utilization during inference tests.
4. Record prompt/context/output token estimates separately.
5. Add index build duration, file count, chunk count, and peak memory.
6. Record image generation duration, size, steps, seed, peak memory, and failure reason.
7. Export a machine-readable profile artifact keyed by Git revision and model hash.

## Operating thresholds

| Signal | Warn | Stop/adapt |
| --- | --- | --- |
| Control API p95 | >100 ms | >250 ms or >1% errors |
| Retrieval p95 | >100 ms | >250 ms |
| Text p95 | >90 s provisional | >120 s or >5% failures |
| Queue depth | >3 for 5 min | >10 or oldest wait >10 min |
| Memory | Sustained swap growth | OOM or host instability |
| SQLite | Write >100 ms | Any failed checkpoint |
| FSM integrity | Any drift warning | Any illegal transition |

## Capacity decision record

Current decision: keep `BONSAI_MAX_CONCURRENT_RUNS=1`. The system is optimized for predictable, inspectable local work rather than parallel inference. Revisit only with a complete 30-run profile and text/image overlap test.
