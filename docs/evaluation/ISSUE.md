# Build an artifact-first creative workflow for treatments → storyboard → film

## Problem

The production pipeline can make three validated 90-second buyer-persona films,
but Bonsai Workbench cannot represent or operate that workflow. A storyboard
request currently completes as a generic HTML page.

Observed evidence:

- 23 Workbench jobs: 17 reviewable and 6 failed (26.1%).
- Failure classes include restart, timeout, missing variable, and incomplete
  HTML.
- The retained storyboard run is a complete HTML document but has no persona,
  Campbell arc, scenes, beats, timing, transitions, continuity, provider
  candidates, narration, or timeline.
- The same run contains duplicate IDs, mojibake, and generic fallback copy.
- The external film pipeline validates 3 films, 90 stills, 270 seconds, and
  6,480 rendered frames.
- Both Bonsai and OpenAI provider cuts exist.
- Audio repair, score, story cards, and burned captions exist, but captions use
  proportional word timing rather than forced alignment.

## Proposed decision

Adopt RFC-0002's typed artifact graph:

```text
Brief → Treatment → Scene → Shot → MediaCandidate
      → Timeline → Verification → Approval → Export
```

Models propose content. Deterministic services validate, compose, compare, and
export it. Every node is addressable, versioned, and recoverable.

## User journey

1. Orient with starter journeys and examples of their outputs.
2. Prompt with a brief and references.
3. Configure duration, provider/privacy policy, style, and budget only when
   needed.
4. Review and confirm the treatment.
5. Review an ordeal-shot pilot across providers.
6. Generate the remaining board with bounded concurrency.
7. Review continuity and acceptance warnings.
8. Repair one scene, shot, narration segment, caption cue, or score layer.
9. Approve the timeline.
10. Export storyboard, manifests, assets, captions, stems, and movie.

## Acceptance criteria

- [ ] A storyboard task cannot complete as generic HTML.
- [ ] Treatment, scene, shot, candidate, timeline, verification, and approval
  have typed schemas.
- [ ] Existing film manifests can be imported without data loss.
- [ ] Human approval is required before full provider fan-out.
- [ ] Provider candidates are comparable at shot granularity.
- [ ] Failed shots can be regenerated without discarding accepted nodes.
- [ ] Local resource classes enforce bounded concurrency.
- [ ] Captions use forced alignment or display an estimated-timing warning.
- [ ] Long unintended silence blocks final approval.
- [ ] Continuity failures can be attached to a specific shot and criterion.
- [ ] Final exports are reproducible from retained versions and asset hashes.
- [ ] The Director's table is the default; Evidence ledger and Cut room are
  addressable secondary views.

## Architectural questions

1. Is SQLite plus a resource-aware queue enough for the next two releases?
2. Which nodes are immutable, and which references may move?
3. Should provider policy select the least expensive passing candidate
   automatically or only recommend it?
4. What alignment engine can run locally with word timestamps?
5. Can Bonsai Image accept reference conditioning, or must continuity remain a
   prompt/seed/review loop?
6. What is the minimal evaluation set that proves the three buyer stories retain
   their hero, ordeal, and return?

## Evidence

- `docs/evaluation/README.md`
- `docs/evaluation/scorecard.json`
- `docs/evaluation/RFC-0002-CREATIVE-ARTIFACT-GRAPH.md`
- `docs/evaluation/DESIGN-TREATMENTS.md`
- `docs/evaluation/assets/`
