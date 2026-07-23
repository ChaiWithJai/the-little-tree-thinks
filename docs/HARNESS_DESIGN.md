# Bonsai Workbench: verification-first harness

The first Bonsai Agent interface was a chat surface with citations. That made the
model response the product and pushed verification into a long evidence list. The
evaluation harness reverses that relationship: the response is one artifact inside a
repeatable human review workflow.

## Design basis

The design follows the central claim in Hamel Husain's *“It's Hard to Eval” Is a
Product Smell*: if the builder cannot cheaply verify an artifact, the user probably
cannot either. The harness therefore asks four questions for every run:

1. What does the reviewer need to check?
2. What trusted local source can they compare it against?
3. What smaller units can they inspect and judge?
4. What review signal should be retained for the next evaluation?

The local Nada Sadhana screenshots contribute the interaction rhythm. They do not use
an open-ended chat loop; they move through explicit states, expose progress, make the
person perform the consequential action, and end with a retained result. Bonsai
Workbench adopts that rhythm as **Case → Run → Inspect → Review → Retain**.

Hex's linked chat and notebook examples contribute progressive disclosure: a concise
artifact first, then the full trace, inputs, sources, and intermediate checks. Devin's
testing recordings reinforce that verification artifacts should save the reviewer from
reproducing the work.

## Core objects

| Object | Purpose | Human action |
|---|---|---|
| Case | Stable question, corpus, and intent | Select or define |
| Run | Immutable model/retrieval attempt | Reproduce or compare |
| Artifact | Answer or generated image | Inspect |
| Evidence | Ranked local source chunks | Open and compare |
| Trace | Model, latency, query, checks | Diagnose |
| Review | Verdict, issue taxonomy, note | Pass, revise, or fail |

## Interaction rules

- Chat is not the top-level navigation or the primary output container.
- Citations are controls: selecting one opens the exact supporting source chunk.
- Automated checks are visible but never impersonate human judgment.
- Errors belong to the system and preserve the retrieved evidence.
- A run is not complete until it is reviewed or deliberately left open.
- Reviews persist locally and appear in run history, creating an evaluation dataset.
- Image generation uses the same artifact logic: fixed prompt, seed, steps, output,
  and an eventual human verdict—not an ornamental generator beside chat.
- Runtime failures and capability boundaries live in a System view rather than
  dominating the main task.

## Current evidence boundaries

Text synthesis, lexical retrieval, citations, persisted run reviews, and local image
generation are live. Claim-level entailment remains a human review task. Bionic's
embedding worker, GGUF runtime, and 27B vision-answer path remain limited as documented
in `BIONIC_LOCAL_REVERSE_ENGINEERING.md`.
