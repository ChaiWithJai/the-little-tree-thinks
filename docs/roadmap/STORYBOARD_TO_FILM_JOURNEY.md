# Storyboard to film journey

GitHub delivery issue:
[issue 5](https://github.com/ChaiWithJai/the-little-tree-thinks/issues/5)

## Problem

The Day 0 screen offers "Build a storyboard," but the current router sends that
request to the HTML page generator. The result can be a polished page without a
treatment, scene contract, shot list, continuity plan, narration, or timeline.

The three buyer films in the sibling `whatif` production prove that the output
is possible. They also show why a single prompt and a single artifact are not
enough.

## User outcome

A user should be able to give Bonsai a brief and receive a 90 second film
without managing production scripts by hand. The user should approve the story
and one representative visual before the system starts the full media run.

## Journey

1. Orient. The user chooses "Make a story film" or describes that result.
2. Brief. The user adds the audience, job, evidence, duration, and references.
3. Treatment. The agent proposes the buyer arc and the user approves it.
4. Board. The agent creates scenes, shots, timing, continuity rules, and
   narration spans.
5. Pilot. The system makes one ordeal shot with each allowed provider.
6. Compare. The user chooses a candidate and approves the visual rules.
7. Produce. The scheduler runs a limited number of image and audio jobs.
8. Review. The user sees the board, failed checks, and exact repair actions.
9. Timeline. The system assembles accepted images, motion, narration, captions,
   story cards, score, and export settings.
10. Export. The user approves an exact dependency set and receives the movie,
    captions, audio, and manifest.

## Current adapters to reuse

1. Bonsai Image can create local candidates.
2. The local retrieval path can ground a brief in private sources.
3. SQLite can remain the local metadata store.
4. The current job UI can show queue and failure states.
5. The current review controls can become scoped artifact decisions.
6. The sandboxed preview can show a storyboard and read only timeline.

## Adapters to add

1. Liquid LFM2.5 Audio for segment narration.
2. A speech alignment adapter for word timestamps.
3. FFmpeg or Editframe for deterministic composition.
4. An optional OpenAI image adapter with an explicit outbound data approval.
5. Media checks for duration, codecs, silence, caption drift, and missing files.

## Required storage changes

The implementation should follow
`docs/evaluation/RFC-0002-CREATIVE-ARTIFACT-GRAPH.md`.

1. Store immutable artifact revisions and content addressed assets.
2. Append assertions and user decisions instead of overwriting them.
3. Replace daemon only execution with leased jobs, attempts, and idempotency.
4. Derive project readiness from the accepted dependency set.

## Acceptance criteria

1. A storyboard request cannot finish as generic HTML.
2. A treatment approval names an exact revision.
3. Full media generation cannot begin before a pilot decision.
4. Bonsai and OpenAI candidates can be compared against one shot contract.
5. Local image and Liquid audio jobs cannot compete for the same device slot.
6. One failed shot or narration segment can be replaced without changing
   accepted siblings.
7. Caption checks use waveform alignment and show estimated timing when needed.
8. Long unintended silence blocks final approval.
9. Remote generation cannot begin without a recorded outbound data decision.
10. Every export contains the accepted revisions, asset hashes, checks, tool
    versions, and settings needed to rebuild the cut from retained media.

## Out of scope for the first release

1. A general video editor.
2. Multi user collaboration.
3. Distributed workers.
4. Autonomous publishing.
5. A promise that remote image generation will reproduce the same pixels.
