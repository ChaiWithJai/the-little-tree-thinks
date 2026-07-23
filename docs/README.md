# Documentation map

Use this page to find the current product contract, implementation notes,
evidence, and history.

## Start here

1. `DAY_ZERO_UX.md` explains the first use experience.
2. `HARNESS_ARCHITECTURE.md` explains the current local app.
3. `roadmap/STORYBOARD_TO_FILM_JOURNEY.md` defines the next user journey.

## Product

| Document | Purpose |
|---|---|
| `PRD_AGENT_HARNESS.md` | Problem and user requirements for the current harness |
| `HARNESS_DESIGN.md` | Interface design decisions |
| `DAY_ZERO_UX.md` | Orient, prompt, work, review, and use stages |
| `STATE_ROUTING.md` | URL, draft, job, run, and cache behavior |

## Architecture and operations

| Document | Purpose |
|---|---|
| `HARNESS_ARCHITECTURE.md` | Current code boundaries and local persistence |
| `RFC_AGENT_HARNESS.md` | Prototype execution state machine |
| `WORKLOAD_PROFILE_AGENT_HARNESS.md` | Reference host capacity and test plan |
| `BIONIC_LOCAL_REVERSE_ENGINEERING.md` | Tested runtime paths and failures |
| `workload-profile-baseline.json` | Machine readable baseline |

The prototype execution RFC describes the app that exists today. The creative
artifact RFC in `evaluation/` defines the replacement for story and film work.

## Creative agent

| Document | Purpose |
|---|---|
| `evaluation/README.md` | Current versus target evaluation |
| `evaluation/PROOF.md` | Visible evidence and checksums |
| `evaluation/RFC-0002-CREATIVE-ARTIFACT-GRAPH.md` | Target artifact and job model |
| `evaluation/DESIGN-TREATMENTS.md` | Three interface directions |
| `roadmap/STORYBOARD_TO_FILM_JOURNEY.md` | Delivery contract for issue 5 |

## Decisions

`decisions/` contains accepted decisions that explain why the repository or
architecture changed. Start with
`decisions/0001-reframe-around-the-creative-agent.md`.

## Archive

The original field study is under `../archive/field-study-v1/`. It is retained
evidence and is not the current setup guide.
