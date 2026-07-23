# Evaluation source manifest

This manifest records the evidence inputs used on 2026-07-23. Private absolute
paths are omitted. Copied screenshots under `assets/` make the review package
portable.

## Bonsai Workbench

- Repository: this repository
- Run database: `.bonsai-agent/evaluations/runs.sqlite3`
- Storyboard run: `0e24330a9fec486b88df4f733f8803c1`
- Storyboard artifact:
  `.bonsai-agent/pages/page-0e24330a9fec486b88df4f733f8803c1.html`
- Workbench interface: `web/`
- Harness implementation: `bonsai_harness/`

## Buyer-persona films

- Repository: sibling `whatif` checkout
- Treatments: `docs/bonsai-buyer-persona-treatments.md`
- Production root: `productions/bonsai-persona-films`
- Story and shots: `productions/bonsai-persona-films/films.json`
- Continuity: `productions/bonsai-persona-films/continuity.json`
- Validation:
  `productions/bonsai-persona-films/tools/validate-production.mjs`
- Narration:
  `productions/bonsai-persona-films/tools/generate-narration.mjs`
- Post-production:
  `productions/bonsai-persona-films/tools/post-produce-films.mjs`
- Provider comparison:
  `productions/bonsai-persona-films/films/airplane-mode/comparisons/comparison.json`
- Polished outputs: `productions/bonsai-persona-films/output/polished/`

## Brief inputs

- Bonsai, Campbell, and buyer persona mapping from a local brief attachment.
- Standalone Workbench source content from a local brief attachment.
- Natural Uniform creative source from a local brief attachment.

## Commands used

```bash
node ../whatif/productions/bonsai-persona-films/tools/validate-production.mjs
ffprobe -v error -show_entries format=duration:stream=index,codec_type,codec_name,duration <movie>
ffmpeg -hide_banner -i <movie> -af silencedetect=noise=-42dB:d=0.8 -f null -
```

## Interpretation boundary

No local artifact identified itself as an output from “Sol 5.6.” The target
treatment and target rubric are therefore inferred acceptance criteria. The
package never presents them as measured model output.
