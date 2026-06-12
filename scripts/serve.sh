#!/usr/bin/env bash
# Serve Ternary-Bonsai locally on stock llama.cpp (OpenAI-compatible API :8080).
# Default: F16 + Metal. "tq2": TQ2_0 + CPU (Metal has no TQ2_0 kernels — do not offload).
set -euo pipefail
MODELS="$(cd "$(dirname "$0")/../models" && pwd)"

if [ "${1:-f16}" = "tq2" ]; then
  exec llama-server -m "$MODELS/Ternary-Bonsai-1.7B-TQ2_0.gguf" \
    --port 8080 --host 127.0.0.1 -ngl 0 --alias ternary-bonsai-1.7b
else
  exec llama-server -m "$MODELS/Ternary-Bonsai-1.7B-F16.gguf" \
    --port 8080 --host 127.0.0.1 -ngl 99 --alias ternary-bonsai-1.7b
fi
