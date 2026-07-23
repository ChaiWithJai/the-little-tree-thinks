# Independent architecture review

- Review date: 2026-07-23
- Review style: read-only, Mitchell Hashimoto-inspired systems critique
- Verdict: **approve the product direction; request substrate changes before
  implementation**

## Evidence considered

- The target comparison is explicitly inferred, not a measured Sol 5.6 run.
- The validated production has three films, 90 stills, and 6,480 delivery
  frames.
- The Workbench produced generic HTML for a storyboard request and had 6 failed
  jobs out of 23 observed jobs.
- The current repository stores whole job/run snapshots as JSON, mutates reviews
  in place, and executes daemon threads behind a global semaphore. That is useful
  demonstration durability, not yet a crash-safe artifact workflow.

## Decisions affirmed

1. Treat Workbench as an artifact orchestrator, not a general chat or full NLE.
2. Let models propose while deterministic systems validate, compose, and export.
3. Keep shot contracts provider-neutral and comparison shot-scoped.
4. Require a human pilot gate before expensive fan-out.
5. Retain accepted media immutably by content hash.
6. Use SQLite and a resource-aware local scheduler for the next two releases.
7. Make the Director's table primary and technical evidence addressable.
8. Animate 30 accepted stills into 2,160 delivery frames; do not generate 2,160
   independent diffusion images.
9. Treat alignment as evidence and visibly label estimated captions.

## Required changes

The original RFC made domain nodes share one lifecycle. That creates impossible
transitions: an approval is never generating and a verification is never
composing. The corrected substrate is:

```text
immutable ArtifactRevision + Edge + Asset
append-only Assertion + Decision + Event
leased Job
mutable Alias / ProjectHead
```

Jobs have execution state. Artifacts have immutable revisions. Decisions bind
exact revisions. Project readiness is a derived projection. The v1 provider
policy recommends a candidate but requires a human to select it. The queue must
have leases, attempts, idempotency, cancellation, and restart recovery.

## Foundational ADRs

Implementation should not start until these first six decisions are accepted:

1. artifact identity, revision, alias, and dependency semantics;
2. separate job, decision, and derived-readiness state models;
3. SQLite schema, migrations, backup, rollback, and single-writer policy;
4. filesystem CAS atomic write, integrity, retention, and disk-full behavior;
5. job leases, heartbeat, attempts, idempotency, cancellation, and recovery;
6. shared-device resource admission and exclusivity groups.

Follow-on ADRs should cover provider capabilities, egress consent, assertions,
decision scope and staleness, legacy import fidelity, export reproducibility,
caption alignment, continuity limits, preview security, scale-up triggers, and
the golden evaluation protocol.

## Smallest coherent v1

- One local operator, one host, one project at a time.
- Fixed eight-scene, 30-shot film template.
- SQLite WAL metadata plus filesystem content-addressed assets.
- One polling worker claiming leased jobs transactionally.
- Existing Bonsai, OpenAI, Liquid, Editframe, and FFmpeg paths behind typed
  adapters.
- Director's table, shot compare, evidence view, and a read/repair timeline.
- No multi-user collaboration, distributed workers, general drag-and-drop NLE,
  autonomous publishing, or claimed pixel-perfect generation.

The flow is import → typed story revisions → treatment approval → one ordeal
candidate per provider → assertions and human pilot decision → bounded shot
jobs → candidate selection → narrow timeline compile → segment TTS, alignment,
and score → audio/caption/export assertions → exact-closure approval → atomic
export.

## Failure contract

| Failure | Detection | Recovery truth |
|---|---|---|
| Process crash | expired lease/heartbeat | retry attempt; preserve upstream approvals |
| Blob written before DB commit | orphan scan | reattach or collect after grace period |
| Missing/corrupt blob | hash check | block only its dependency closure |
| Local memory contention | admission metrics | queue for capacity; do not call it model failure |
| Provider timeout | typed adapter error | bounded retry or provider alternative |
| Duplicate paid request | idempotency/request IDs | reconcile before retry |
| Stale approval | dependency-closure mismatch | append a new decision for affected scope |
| TTS silence/caption drift | waveform and alignment gates | repair exact segment |
| Partial export | temp bundle and closure check | publish only after atomic verification |
| Remote privacy risk | egress gate and payload hash | no cloud call without recorded consent |

## Go / no-go

Go to a pilot only when all three production packages import without lost files;
storyboard requests cannot route to generic HTML; approvals bind revision IDs;
crash injection preserves accepted artifacts; Bonsai and OpenAI candidates share
one shot contract; local diffusion and audio cannot collide; targeted visual and
audio repair works; and remote egress always has recorded consent.

Go to v1 when the three films complete through Workbench without manual file
surgery; every export has a closed manifest and toolchain versions; media,
silence, alignment, and missing-asset checks block release; approvals become
visibly stale; and restart, disk-full, blob-corruption, timeout, and low-alignment
tests fail safely.

No-go while accepted content can be overwritten, execution depends only on
daemon threads, jobs lack leases and idempotency, database/blob writes are not
atomic, cloud egress is silent, approval scope is ambiguous, estimated captions
look authoritative, or exports omit retained hashes and toolchain versions.
