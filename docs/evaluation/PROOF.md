# Proof ledger

This page makes the evidence in PR #4 visible and separates what the pull
request can reproduce from what was observed in the local production.

## 1. The current journey returns the wrong artifact type

**Claim:** the “Build a storyboard” journey completed as generic editorial HTML,
not a treatment, scene graph, shot board, or timeline.

![Current Workbench storyboard run](assets/bonsai-storyboard-run.png)

![Current generated HTML artifact](assets/bonsai-storyboard-artifact.png)

The screenshot is the observed Workbench run. The machine-readable scorecard
records 23 jobs, 17 reviewable jobs, and 6 failures. The CI validator checks that
the totals reconcile and that this evidence file has the retained SHA-256 hash.

## 2. The proposed target makes creative stages addressable

**Claim:** the proposed interface can expose the treatment, board, provider
comparison, narration, timeline, verification, and export as distinct stages.

![Declared target contract](assets/sol-5-6-target-contract.png)

![Declared target contract at 390 pixels](assets/sol-5-6-target-mobile.png)

This is a rendered design treatment, not an observed Sol 5.6 result. It is
deliberately labeled as an inferred target contract in the page, scorecard, and
PR.

## 3. The provider delta is visible at the same story beat

**Claim:** at the ordeal beat, the recorded OpenAI candidate better satisfies
gesture and clean-overlay criteria while Bonsai retains the illustrative local
style.

![OpenAI left, Bonsai right](assets/provider-delta-openai-left-bonsai-right.png)

The same-shot comparison is stronger evidence than comparing unrelated hero
frames. The scorecard preserves the finding and the three film contact sheets
show the broader provider pattern.

## 4. Production-scale receipt

The external `whatif` production validator reported:

```text
margin-test: 90s, 30 stills, 150 narration words
new-tenant: 90s, 30 stills, 137 narration words
airplane-mode: 90s, 30 stills, 162 narration words

Production validation passed: 90 stills, 270 seconds, 6,480 rendered frames.
```

Those source movies and generation manifests live in the sibling `whatif`
production and are not included in this PR. This receipt is therefore local
corroboration, not a GitHub-reproducible check.

## 5. What CI proves

The `creative-evaluation-proof` workflow runs the portable validator. It checks:

- every evaluation document and screenshot required by the proof bundle exists;
- the scorecard labels target evidence as inferred;
- Workbench job counts and production frame/still arithmetic reconcile;
- production validation is recorded as passing;
- the lack of forced caption alignment is recorded rather than hidden;
- every rubric score is in range and has an evidence statement;
- the three central screenshots and scorecard match retained SHA-256 hashes.

Expected receipt:

```text
Creative evaluation valid: 22 files, 10 rubric dimensions, 4 proof hashes
```

## 6. Evidence hashes

| Artifact | SHA-256 |
|---|---|
| Current storyboard run | `a37eccefc720a142c7b9e67f813f8303058d3f52a8ea7cab9a25f921fcaab84a` |
| Target contract | `1ff589278ebea6a732df7bcf07407041472eb151244569004681b91b97d50841` |
| Provider delta | `79ebea770c968cc3332091acf411c3c00533746117f6120afda2052218bfc42e` |
| Scorecard | `b0cef2385935c29ac97b7b67f6d37428026c5e91a791ef21642d06a2d86d200f` |

## Evidence boundary

This PR proves the integrity and internal consistency of the retained evaluation
bundle. It does not prove an unavailable Sol run, reproducibility of remote
image generation, or the sibling production’s media pipeline inside GitHub CI.
Those boundaries are explicit so a screenshot cannot masquerade as a benchmark.
