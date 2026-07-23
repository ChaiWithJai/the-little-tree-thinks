# Interface design treatments

The treatments share one information architecture. They differ in how much
complexity is visible at once.

## Treatment A — Director's table

**Best for:** creative operators and stakeholders.

The center of the interface is an eight-scene contact sheet. The selected scene
opens a filmstrip of shots. Story, narration, and acceptance criteria sit in a
calm inspector. Provider candidates appear side by side only when a choice is
needed.

Signature interactions:

- approve the treatment;
- approve the ordeal-shot pilot;
- drag an accepted shot into the timeline;
- ask for one scoped change;
- compare Bonsai and OpenAI against the same gate;
- export a review link or production bundle.

This is the recommended Day 0 direction because it begins with the artifact,
not the pipeline.

## Treatment B — Evidence ledger

**Best for:** model and infrastructure teams.

Every creative artifact is a row in an append-only ledger. The visual board is
paired with provenance: prompt hash, model, seed, runtime, duration, validation,
review, and asset hash. Failures retain completed upstream nodes.

Signature interactions:

- expand a row from story to source evidence;
- filter by failed criterion or provider;
- replay a single job with the same inputs;
- diff prompt, asset, and verdict versions;
- export an evaluation report.

This treatment makes trust the main product. It should remain available as a
secondary view, not become the first-run interface.

## Treatment C — Cut room

**Best for:** post-production and repair.

The interface is a four-track timeline: image/motion, narration, captions/titles,
and score. Each clip links back to its scene, shot, candidate, and verification
record. Warnings are temporal: silence, caption drift, unsafe text area, identity
change, or missing transition.

Signature interactions:

- listen to narration by segment;
- realign a caption cue;
- replace one still while preserving timing;
- preview chapter cards and safe areas;
- render a 12-second review range;
- export stems, captions, manifest, and master.

This treatment is powerful after the board is approved. Leading with it on Day 0
would expose too much production machinery too early.

## Recommended composition

Use Treatment A as the default, with two addressable secondary views:

```text
Director's table
  ├── Evidence ledger
  └── Cut room
```

The URL owns the durable view and selected artifact:

```text
/projects/:projectId/story
/projects/:projectId/board?scene=:sceneId&shot=:shotId
/projects/:projectId/compare?shot=:shotId
/projects/:projectId/timeline?t=:seconds
/projects/:projectId/evidence?node=:nodeId
```

Draft text, inspector expansion, and playback position remain local until the
user saves or approves them. Server cache stores immutable manifests and media
metadata; large binary assets stay content-addressed on disk.
