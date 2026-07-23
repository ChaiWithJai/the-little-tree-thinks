# PRD: Bonsai local agent harness

| Field | Value |
| --- | --- |
| Document type | Problem Requirements Document |
| Status | Implemented prototype; creative successor planned |
| Owner | Bonsai Workbench |
| Updated | 2026-07-22 |
| Related RFC | `docs/RFC_AGENT_HARNESS.md` |
| Workload evidence | `docs/WORKLOAD_PROFILE_AGENT_HARNESS.md` |

HashiCorp describes a PRD as the document that defines the problem and the “why,” followed by an RFC that proposes a solution. This document follows that separation: it specifies outcomes and constraints without prescribing the implementation. Reference: [HashiCorp writing practices and culture](https://www.hashicorp.com/en/how-hashicorp-works/articles/writing-practices-and-culture).

## Executive summary

Bonsai has multiple useful local model paths—cited text synthesis, lexical retrieval, and offline image generation—but using them is still a sequence of opaque, long-running calls. The workbench must become a trustworthy agent harness: a person submits a checkable task, watches its real state, inspects every artifact and source, distinguishes infrastructure failures from model failures, supplies human judgment, and can recover without losing completed work.

The product is successful when the operator never has to infer whether a run is queued, retrieving, generating, validating, checkpointing, awaiting review, retained, unreachable, or failed. The UI must reflect one authoritative state machine rather than independently guessing progress from request timing.

## Problem

### Current user problem

The existing local workflow has three failure-producing ambiguities:

1. A synchronous inference request can take 37–54 seconds on the reference machine. During that interval the browser only knows that a fetch is pending.
2. A browser/server connection interruption is rendered like a model synthesis failure. The application may mark retrieval complete and synthesis blocked even when the server never accepted the job.
3. The plan, status pills, activity card, adapters, and persisted run each derive state separately. Contradictory states are therefore possible.

These ambiguities damage trust precisely where the harness is meant to create it. A locally private model is not operationally trustworthy if the person cannot determine what happened, what was saved, or what can safely be retried.

### Evidence

Baseline profiling on the 24 GB Apple M4 Pro reference host shows:

- Control-plane API: 100 requests at concurrency 8, 0 errors, 38.1 ms p95.
- Lexical retrieval: 120 queries over 2,003 chunks, 48.0 ms p95.
- Retained text synthesis: 37.4 s, 44.5 s, and 54.3 s across the three available runs.
- State: 5.0 MB lexical index and 76 KB SQLite database for three runs.

Inference is therefore three orders of magnitude slower than retrieval. Treating both as one browser request is the primary interaction and reliability problem, not control-plane throughput.

## Users and jobs to be done

### Primary: local model operator

When I submit a private task to a local model, I need to see its actual lifecycle and evidence so I can distinguish slow progress from failure and decide whether to trust the artifact.

### Secondary: harness/model developer

When I change an adapter, prompt, model, or retrieval policy, I need comparable retained runs and workload measurements so I can identify regressions without relying on impressions.

### Secondary: reviewer/domain expert

When I review an answer, I need source-level provenance, deterministic checks, and a stable review taxonomy so my judgment becomes reusable evaluation data.

## Goals

1. Make every run state explicit, authoritative, and observable.
2. Wrap heterogeneous local model adapters behind stable contracts.
3. Preserve inspectable artifacts and human review transactionally.
4. Separate control-plane, retrieval, inference, validation, image, and persistence workloads.
5. Provide repeatable workload profiles and capacity gates.
6. Preserve the local-only privacy boundary.

## Non-goals

- General-purpose autonomous coding or unrestricted shell execution.
- Pretending the current process can resume inside an interrupted model call.
- Multi-tenant authentication, billing, or remote SaaS deployment.
- Horizontal inference scaling before one reference host is measured and stable.
- Semantic vector retrieval while the discovered embedding worker remains unavailable.
- Claiming model quality from machine checks alone; human review remains required.

## Requirements

### Functional requirements

| ID | Requirement | Acceptance evidence |
| --- | --- | --- |
| FR-1 | A submitted task becomes a job with a stable ID before inference begins. | `POST /api/jobs` returns HTTP 202 and a `queued` job. |
| FR-2 | The lifecycle has legal, validated transitions. | Contract tests reject an illegal transition and cover the complete happy path. |
| FR-3 | UI status, plan progress, active adapter, and activity copy derive from the same machine state. | A state fixture produces one consistent UI projection. |
| FR-4 | Transport loss is distinct from server/model failure. | A failed poll renders `unreachable`; a job exception renders `failed` with `failed_stage`. |
| FR-5 | Inference concurrency is bounded and excess work queues. | With capacity 1, a second inference job remains `queued` until the first releases capacity. |
| FR-6 | Completed answers, evidence, checks, timing, and reviews are durable. | Restarting the server preserves completed runs and reviews in SQLite. |
| FR-7 | Every cited claim can be traced to the retrieved source chunk. | Citation controls resolve only valid `[S<n>]` identifiers and surface failed validation. |
| FR-8 | Human verdicts use the configured taxonomy. | Unknown issue IDs return HTTP 400; valid review data is retained. |
| FR-9 | Adapter identity and readiness come from the server registry. | The browser contains no model-name source of truth. |
| FR-10 | Text and image workloads remain available as separate adapters. | Runtime status reports both paths independently; one may fail without hiding the other. |
| FR-11 | Operators can retry an interrupted or failed task without overwriting prior sessions. | Retry creates a new job ID and prior runs remain readable. |
| FR-12 | The workload profile is reproducible and read-only by default. | `scripts/profile_harness.py` reports API, retrieval, retained-run, and state-size measurements without creating inference jobs. |

### Non-functional requirements

| ID | Requirement | Initial target on reference host |
| --- | --- | --- |
| NFR-1 | Privacy | No source or prompt traffic outside loopback; image generation forces offline mode. |
| NFR-2 | Control latency | `/api/cases` and `/api/runs` p95 under 100 ms at concurrency 8. |
| NFR-3 | Retrieval latency | Three canonical queries p95 under 100 ms over the current 2,003-chunk index. |
| NFR-4 | Text latency | Establish p50/p95 from at least 30 canonical runs; provisional p95 guardrail 90 s. |
| NFR-5 | Error rate | 0% control-plane errors in 100-request baseline; under 5% model failures across a 30-run soak. |
| NFR-6 | Backpressure | Default maximum of one concurrent text inference on the 24 GB reference host. |
| NFR-7 | State integrity | Illegal state transitions fail closed and never silently advance the plan. |
| NFR-8 | Honest UI | Estimated tokens and ephemeral job state are labeled; no fabricated context limit or durability claim. |
| NFR-9 | Accessibility | Keyboard-operable task, session, evidence, and review controls with visible focus and reduced-motion support. |

## Success metrics

- 100% of terminal failures have a failure class and failed stage.
- 100% of completed model runs have a retained trace and check result.
- 0 contradictory plan/status/activity states in the FSM fixture suite.
- At least 30 canonical text runs collected before changing the provisional inference SLO.
- Human review completion rate and verdict distribution visible from retained data.
- No non-loopback network call during the privacy verification run.

## Product principles

- **Observed, not implied:** Show only states and capabilities the harness can prove.
- **Artifacts before answers:** A result includes evidence, checks, timing, and review—not only prose.
- **Backpressure before scale:** Queue expensive work rather than allowing the host to thrash.
- **Local by construction:** Remote access is a future security decision, not an accidental bind-address change.
- **Recover at stable boundaries:** Retry from a checkpointed task or artifact; do not claim token-level inference resumption.

## Open questions for review

1. Must in-flight jobs survive a process restart, or is durable task input plus retry sufficient for v1?
2. Should text and image inference share one host-wide capacity semaphore or separate device budgets?
3. What benchmark set represents production use beyond the three current cases?
4. Which model-quality checks should gate `awaiting_review` versus merely annotate it?
5. When model selection becomes user-facing, which adapter capabilities must be declared up front?
