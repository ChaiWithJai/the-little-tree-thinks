# ADR 0001: Reframe the repository around Bonsai Workbench

## Status

Accepted on 2026-07-23.

## Context

The repository began as a PrismML developer ecosystem field study. Its root
README presented the study, Nada Sadhana, model measurements, and a DevRel
application.

The working tree later gained a local agent, a browser Workbench, evaluation
cases, retained traces, and a creative production study. Those files were the
active product, but they were not tracked. A new user therefore saw the
historical story instead of the current app.

The creative production also proved that the current HTML storyboard starter
does not represent the full job. A film needs a treatment, scenes, shots, media
candidates, narration, captions, a timeline, review decisions, and an export.

## Decision

The repository root now represents Bonsai Workbench.

1. We track the local agent, web app, tests, evaluation catalogs, and benchmark
   tools as the active codebase.
2. We preserve the original field study under `archive/field-study-v1/`.
3. We keep the creative production evaluation under `docs/evaluation/`.
4. We use a portable example config and ignore private local config files.
5. We allow user named corpora instead of fixed Dharma and civic source names.
6. We describe the current storyboard route as HTML generation until the typed
   creative journey is implemented.

## Deprecated paths

| Deprecated path or promise | Replacement | Removal rule |
|---|---|---|
| Field study README as the product entry point | Root Workbench README | Archived now |
| Field study documents and screenshots in active folders | `archive/field-study-v1/` | Preserved indefinitely |
| Original `scripts/serve.sh` as the main setup | Runtime specific setup in the root README | Preserved in the archive |
| Fixed `dharma` and `civic` corpus names | Corpus names from local config | Removed from active code |
| Storyboard as a generic HTML page | Typed storyboard to film journey | Remove the old starter route after the new journey passes |
| Synchronous `POST /api/run` for browser work | `POST /api/jobs` and job polling | Keep for compatibility until callers are inventoried |
| Whole run JSON snapshots as the final creative store | Immutable artifact revisions and leased jobs | Replace during the creative journey work |

## Consequences

New users can start with the app and see the exact runtime choices. Historical
claims remain available without competing with current setup.

The repository now contains code that was previously local only. Continuous
integration checks the state machine, service contracts, and creative proof
bundle.

The current app is still an evaluation harness with text, HTML, and image
paths. This decision does not claim that the artifact graph, Liquid audio, or
film export already exist. The roadmap and GitHub issue define that work.

## Reversal

Git history retains every moved file. Reversing this decision would require a
new ADR because the root product contract and setup instructions would change.
