# RFC-0002: A typed creative-artifact graph for Bonsai Workbench

- Status: Proposed
- Date: 2026-07-23
- Owners: Bonsai Workbench / What If production
- Related: `docs/RFC_AGENT_HARNESS.md`

## Summary

Replace “prompt in, monolithic artifact out” for creative work with a durable,
typed graph of domain artifacts:

```text
Brief
  → Treatment
  → Scene
  → Shot
  → MediaCandidate
  → Timeline
  → Export
```

Brief, Treatment, Scene, Shot, MediaCandidate, Timeline, and Export are artifact
kinds built on immutable `ArtifactRevision` records. Verification is an
append-only `Assertion`; approval is an append-only `Decision`; generation and
composition are leased `Job`s. These primitives deliberately do not share one
lifecycle. Models propose artifact content; deterministic services validate,
compose, compare, and export it.

## Protocol boundary

Creative intent and media realization are separate stages:

```text
model proposal
  → schema validation and reference resolution
  → human approval when the policy requires it
  → deterministic job adapter
  → recorded observation
  → verification
```

A model may repair an invalid proposal. It cannot bypass schema validation,
approval, resource policy, or the pilot gate.

## Why now

The film production proves the desired output is feasible. It also proves that
the successful workflow exists outside the Workbench:

- treatments live in Markdown;
- stories, narration, scenes, and shots live in JSON;
- providers are called by scripts;
- continuity is a separate JSON contract;
- captions and score are created in post;
- review decisions live in ad hoc comparison metadata;
- final videos are exported by FFmpeg.

The Workbench currently compresses this graph into “Build HTML page.” A
storyboard request can therefore complete while producing no storyboard.

## Goals

1. Make every creative stage inspectable and addressable.
2. Separate semantic inference from deterministic media operations.
3. Allow provider choice and A/B review at shot granularity.
4. Preserve a human approval gate before expensive fan-out.
5. Support targeted repair without discarding accepted work.
6. Export the manifests and media required to reproduce the final cut.

## Non-goals

- Training a new foundation model.
- Generating 2,160 independent images per film.
- Removing human creative direction.
- Claiming pixel-perfect character continuity from text-only diffusion.
- Adopting a general distributed workflow engine before local queue limits
  demand it.

## Substrate primitives

The domain graph is represented by eight small storage primitives:

- `ArtifactRevision` — immutable, schema-versioned content for a logical
  artifact;
- `Edge` — a typed relationship between exact revisions;
- `Asset` — content-addressed retained bytes;
- `Assertion` — a criterion-versioned automated or human observation with
  evidence;
- `Decision` — an accept/reject choice bound to exact revisions and dependency
  hashes;
- `Job` — leased execution with attempts, inputs, resource requirements, and an
  idempotency key;
- `Event` — append-only execution and audit history;
- `Alias` — the only mutable pointer, used for project heads and named views.

Domain objects are schemas over `ArtifactRevision`, not bespoke stateful
classes.

## Domain artifact kinds

### Brief

Source text, attachments, audience, job to be done, required deliverables,
duration, policy, provider constraints, and success criteria.

### Treatment

Logline, buyer-hero, dramatic stakes, arc, ordeal, return, style, proof
requirements, and closing line.

### Scene

Intent, duration, location, characters, narration span, continuity requirements,
and transition.

### Shot

Composition, action, evidence insert, duration, camera move, layer plan, negative
constraints, and acceptance criteria.

### MediaCandidate

Provider, model, prompt hash, input references, seed, dimensions, runtime,
duration, cost class, asset URI, and automated/manual assessment.

### Timeline

Accepted shots, transforms, narration segments, captions, titles, score, stems,
and export settings.

### Assertions

Typed checks:

- story: buyer is hero, ordeal visible, return present;
- continuity: identity, wardrobe, environment, palette;
- image: composition, gesture, screen surface, text policy;
- audio: duration, loudness, long-silence windows, clipping;
- captions: text equality, alignment confidence, line length, safe area;
- export: duration, fps, codecs, dimensions, fast-start, checksum.

### Decisions

Decision, reviewer, timestamp, scope, note, and the exact artifact revisions and
dependency hashes covered.

## Execution events

Job state and project readiness are derived from an append-only event log. The
minimum event types are:

- `JobTransitionEvent`
- `ToolActionEvent`
- `ObservationEvent`
- `VerificationEvent`
- `UserDecisionEvent`
- `WorkflowErrorEvent`

Every event records:

- event ID and timestamp;
- job ID, artifact revision IDs, and attempt;
- causation and correlation IDs;
- actor or role;
- adapter and environment version;
- idempotency key;
- input and output asset hashes;
- privacy and provider policy decision.

`WorkflowErrorEvent` distinguishes retryable tool failure, node-terminal failure,
and workflow-fatal failure. A provider timeout is not a conversation failure. A
failed shot is not a failed treatment.

## Role and capability manifests

Roles are policy, not only prompt prose:

| Role | May propose | May execute | Default approval |
|---|---|---|---|
| `director` | treatment, scene, shot intent | no media mutation | treatment and pilot |
| `producer` | job plans and provider routes | approved job adapters | full fan-out |
| `verifier` | checks and repair recommendations | read-only inspection | none |
| `composer` | timeline and export plan | deterministic media composition | final export |

Each manifest declares allowed node types, tools, providers, privacy classes,
resource class, model/reasoning setting, maximum turns, skills, and approval
policy. Permission to use a remote provider is scoped to exact artifact
revisions and input asset hashes; it is not inherited implicitly from a parent
conversation.

## State models

```text
Job: queued → leased → running → succeeded | failed | cancelled
Decision: append accept | reject against exact revision IDs
Project readiness: derived needs_review | ready_to_compose | export_blocked
```

Artifact revisions and assets are immutable and therefore do not transition.
Changing an upstream artifact creates a new revision; its dependency closure
makes affected decisions visibly stale without mutating their history. A failed
shot job does not invalidate an accepted treatment or narration revision.

## Canonical state and context views

The artifact graph and append-only event log are canonical. Agents receive
role-specific projections that may condense old logs and rejected candidates.
Condensation must never replace or summarize away:

- accepted criteria;
- approval scope;
- artifact revision IDs;
- asset hashes;
- provider provenance;
- privacy decisions.

This separates context-window management from product truth.

## Scheduling and parallelism

Use a bounded local scheduler with resource classes:

| Resource class | Default concurrency | Examples |
|---|---:|---|
| `cpu-light` | 4 | manifests, validation, caption formatting |
| `disk-heavy` | 1 | final encode, asset synchronization |
| `local-llm` | 1 | Bonsai text inference |
| `apple-gpu-heavy` | 1 | Bonsai Image or Liquid narration |
| `remote-provider` | 2 | OpenAI image calls |

The scheduler may overlap CPU validation with a remote request. It should not
assume local diffusion and local TTS are safe to saturate concurrently. Resource
admission uses capacity and exclusivity groups, plus memory and disk preflight,
so two nominally different adapters cannot collide on one constrained device.

## Pilot gate

Before fan-out:

1. choose one representative ordeal shot;
2. generate one candidate per allowed provider;
3. verify story, identity, gesture, style, and clean-overlay requirements;
4. obtain human approval for the visual contract;
5. lock prompt template and continuity version;
6. enable the remaining jobs.

The existing full-run confirmation flag becomes a durable decision bound to the
pilot candidate, treatment revision, continuity revision, and dependency hashes.

## Caption alignment

The current proportional allocator is an acceptable fallback, not a truth
source. Add an alignment adapter:

```text
narration.wav + exact script
  → word timestamps + confidence
  → caption chunks constrained by reading speed and line length
  → visual QA frame samples
```

Confidence is diagnostic rather than the sole gate. The final gate checks script
coverage, monotonic timestamps, maximum segment drift, reading rate, and
long-silence windows. If timing is estimated or any check fails, label captions
“estimated” and block final approval unless a reviewer records a scoped override
and reason.

## Provider policy

Do not select one provider for an entire film by default.

1. Generate provider-neutral shot contracts.
2. Route by privacy, capability, cost, and prior pass rate.
3. Compare candidates against the same acceptance criteria.
4. Recommend a candidate using the declared privacy, cost, and quality policy.
5. Escalate only the failed shot to a stronger or remote provider.

This preserves Bonsai's local advantage while using OpenAI where gesture,
typography, or screen fidelity is decisive. For the three-film v1 rollout, a
human binds the selected candidate; automatic acceptance is deferred until pass
rates are calibrated.

## Interface contract

The primary result view has five layers:

1. **Story** — treatment, eight-scene spine, narration.
2. **Board** — contact sheet with status and continuity warnings.
3. **Compare** — same shot, multiple providers, same criteria.
4. **Timeline** — image, motion, narration, captions, titles, score.
5. **Evidence** — prompts, model/runtime metadata, logs, checksums.

Technical detail uses progressive disclosure. The primary action is always
scoped: approve treatment, approve pilot, regenerate shot, realign captions,
render preview, or export.

## Persistence

Use SQLite in WAL mode with a single writer for metadata and events. Store large
media in a filesystem content-addressed store. Write a blob to a temporary file,
flush and hash it, atomically rename it, then commit metadata. Verify hashes on
read and export; scan for missing and orphaned blobs.

Do not store generated binaries inside JSON. Do not overwrite accepted assets.

The minimum tables are:

```text
projects
artifact_revisions(id, logical_id, kind, schema_version, body_json, content_hash)
edges(from_revision, relation, to_revision)
assets(hash, media_type, bytes, relative_path)
jobs(id, kind, state, input_revision_ids, resource_group, idempotency_key,
     attempt, lease_owner, lease_expires_at, error_json)
job_events(job_id, seq, state, at, details_json)
assertions(target_revision, criterion_id, criterion_version, verdict, evidence_json)
decisions(scope, target_revision_ids, verdict, reviewer, at, note)
aliases(project_id, name, revision_id)
```

A polling worker claims jobs transactionally by lease. Expensive generation
runs in supervised subprocesses or external adapters, not daemon threads in the
web process. Adapters expose capabilities, prepare, execute, collect, and cancel
operations and return typed provenance.

Persist normalized tool inputs, observations, transition results, adapter and
environment versions, and a checkpoint after every event. Replay supports:

1. dry-run validation without provider calls;
2. rebuilding derived views from the event log;
3. recomposing from retained assets;
4. rerunning recorded generation inputs.

Nondeterministic generation is reproduced by reusing content-addressed outputs
or rerunning recorded inputs. The system does not promise identical regenerated
pixels.

## Security and privacy

- Preserve local-only briefs and media by default.
- A remote provider decision must be visible before transmitting prompt or
  reference material.
- Record the exact outbound payload hash, provider, retention implications,
  redactions, and reviewer consent before a cloud call.
- Redact absolute source paths from exported reports.
- Keep raw prompts and provider responses locally for reproducibility.
- Sandboxed HTML previews must not gain access to local files or parent state.

## Prior-art comparison

| Harness | Mechanic to borrow | Mechanic not to cargo-cult |
|---|---|---|
| Codex | Bounded subagents, inspectable threads, configurable roles and concurrency, and caution around parallel writes | A consolidated conversational answer as durable creative state |
| OpenHands | Typed append-only events, explicit error classes, condensed views, and a sandboxed client/server runtime | A conversational step as an artifact graph; Docker isolation for every local transform |
| Aider | Architect/editor responsibility separation and strict realization formats | A second free-form model as the default media executor |
| SWE-agent | Small typed agent-computer interfaces plus persisted trajectories and replay | Bash/file state as a universal multimodal interface |
| Claude Code | Declarative agent capabilities, permissions, hooks, and isolated work | Parent-session permission as authorization to send a specific brief or asset remotely |

Primary references:

- [Codex subagents and best practices](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [OpenHands agent architecture](https://docs.openhands.dev/sdk/arch/agent)
- [OpenHands runtime architecture](https://docs.openhands.dev/openhands/usage/architecture/runtime)
- [Aider architect mode](https://aider.chat/docs/usage/modes.html)
- [SWE-agent repository and ACI](https://github.com/SWE-agent/SWE-agent)
- [Claude Code CLI controls](https://docs.anthropic.com/en/docs/claude-code/cli-usage)

Comparison checked 2026-07-23. SWE-agent is in maintenance-only mode and points
new development to mini-SWE-agent; this RFC borrows the ACI principle rather than
its current implementation.

## Alternatives considered

### Keep monolithic generation and improve the prompt

Rejected. The recorded storyboard request produced valid HTML with the wrong
semantic artifact. Prompting alone cannot make partial repair, provenance, and
stage-level approval durable.

### Let the strongest model generate the entire project

Rejected. The pipeline includes deterministic media work, provider policies,
human approval, and resource constraints that should not depend on model memory.

### Use one autonomous manager with many workers

Deferred. Most stages form a dependency graph, not independent creative tasks.
Parallelize only candidate generation and bounded read-heavy review.

### Adopt Temporal or another workflow engine now

Deferred. SQLite plus a resource-aware local queue is sufficient until multiple
machines, multi-user execution, or durable remote workers become requirements.

## Rollout

1. Accept ADRs for artifact identity, split state models, SQLite migration,
   filesystem atomicity, leased jobs, and device admission.
2. Add substrate tables and domain schemas for Brief, Treatment, Scene, Shot,
   Candidate, Timeline, Assertion, and Decision.
3. Import the existing `films.json`, continuity file, shot manifests, narration
   manifests, and comparison record.
4. Add treatment and board views without changing generation.
5. Move provider scripts behind typed leased job adapters.
6. Add pilot approval and shot-level regeneration.
7. Add waveform alignment and measurable caption gates.
8. Add a narrow timeline compiler and atomic export bundle.
9. Evaluate the same three persona films through the Workbench.

## Acceptance criteria

- A storyboard request cannot complete with only generic HTML.
- A reviewer can approve the treatment and pilot independently.
- A failed shot can be regenerated without changing accepted shots.
- Every provider candidate records provenance and criteria results.
- Captions have timestamp confidence or are explicitly marked estimated.
- Long unintended silence is a blocking audio check.
- The final export is reproducible from retained artifact revisions, asset
  hashes, compositor/FFmpeg and font versions, and settings. Remote generation
  itself is not promised to reproduce identical pixels.
- Restart, timeout, disk-full, corrupt-blob, and stale-approval fault injection
  preserves accepted work and exposes a scoped recovery action.
