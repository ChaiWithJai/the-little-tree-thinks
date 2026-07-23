# Bonsai Local — Validated Setup (M4 Pro, 24GB)

Local inference for PrismML's Ternary-Bonsai, feeding `gemini-music`'s refactored
`bonsai_adapter` / `bonsai_scoring` services. Everything here runs on **stock Homebrew
llama.cpp** — no forks, no untrusted code.

## TL;DR

```bash
brew install llama.cpp
./scripts/serve.sh          # F16 + Metal (default): 125 t/s, 3.2GB
./scripts/serve.sh tq2      # TQ2_0 + CPU: 111 t/s, 590MB  ← the density play
```

Then in gemini-music:

```bash
USE_BONSAI_ADAPTATION=true USE_BONSAI_SCORING=true \
BONSAI_SERVER_URL=http://127.0.0.1:8080 make run
```

## Models (`models/`)

| File | Size | Status |
|---|---|---|
| `Ternary-Bonsai-1.7B-F16.gguf` | 3.2GB | ✅ works, Metal, 125 t/s |
| `Ternary-Bonsai-1.7B-TQ2_0.gguf` | 590MB | ✅ works, **CPU only** (`-ngl 0`), 111 t/s. Made here via mainline `llama-quantize F16 → TQ2_0` |
| `Bonsai-8B-Q1_0.gguf` | 1.1GB | ❌ unusable on stock llama.cpp (degenerate fallback path, ~minutes/token). Needs PrismML's fork |

## Footguns (all verified empirically — see docs/JOURNEY.md)

1. **Two "Bonsai" models exist.** `deepgrove/Bonsai` (0.5B, 2025) ≠ `prism-ml/Bonsai-*`
   (1.7B/4B/8B, 2026). AI-generated summaries blend their specs. Always check the org prefix.
2. **PrismML's Q1_0 and custom "Q2_0" GGUFs require their llama.cpp fork.** Stock llama.cpp
   *loads* Q1_0 without erroring, then runs ~1000x slow. Silent, not loud, failure.
3. **Mainline TQ2_0 requantization of the F16 works** (2.88 BPW, output verified coherent)
   — but Metal has no TQ2_0 kernels: `-ngl 99` aborts ("Asserting on type 35"). Use `-ngl 0`.
4. **Small ternary models can't freehand JSON.** The gemini-music integration enforces
   schemas at decode time via llama-server's `response_format: json_schema` (grammar
   sampling). Values still get clamped/validated server-side.
5. **Sampling matters**: model card says temp 0.5, top-k 20, top-p 0.85. Defaults drift.
6. The chat template injects a Qwen3-style `<think>` block; grammar-constrained requests
   suppress it, raw completions include it. Don't parse raw output naively.
