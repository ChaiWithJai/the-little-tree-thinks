# Bionic: local evidence map (2026-07-22)

This is an interoperability map, not an attempt to bypass Bionic safeguards or inspect
anything outside the local installation and user-owned state.

## What is observable locally

Bionic 1.0.2+3 is LM Studio's Electron desktop app. Its packaged local code exposes
project/workspace sessions, local document parsing, retrieval, embedding, model loading,
MCP, and tool execution namespaces. Its user state stores projects, sessions, parsed
document cache, retrieval sessions, conversation state, and local model metadata under
`~/.lmstudio/apps/bionic` and `~/.lmstudio/.internal`.

The intended loop is therefore:

1. create/open a project;
2. attach local files and parse them into chunks;
3. select an embedding model and retrieve relevant chunks;
4. run a local model in a session with tools and citations;
5. retain project/session state locally.

## Exact Bionic use cases, from the local product surface

The locally running Bionic UI exposes an **agent workspace**, rather than a generic
single-prompt model console. Its visible controls and installed namespaces establish
these uses:

| Use case | Local evidence | What it means for Bonsai Agent |
|---|---|---|
| Project-aware research | Project workspace, sessions, attached files, parsed-document cache, retrieval sessions | Good conceptual match for the Dharma and civic corpora. |
| Tool-using coding/research agent | Bionic's allowed file, browser, terminal, image-viewing and Python tools are injected into sessions | Ternary Bonsai is marked `trainedForToolUse`; it needs a working tool-call runtime, not a bare RAG completion endpoint. |
| Local multimodal review | The installed 27B MLX and GGUF records both declare `vision: true`; the GGUF includes an mmproj file | This is image *understanding* capability, not evidence of an image generator. |
| Local retrieval / grounding | `retrieval`, `embedding`, `internalDocumentParsing`, project and citation schemas are packaged locally | It can be the reference architecture, but its embedding worker must load before it can be the live semantic index. |

There is no local evidence that **Bionic itself** is intended to be a standalone
image-generation application. A separate local PrismML `bonsai-image-demo` installation
does contain Bonsai Image 4B ternary MLX weights, but that is a distinct app/runtime,
not a Bionic capability. The correct Bionic product claim is therefore **local image
analysis when the vision runtime works**, not image generation.

## Tested on this machine

| Capability | Evidence | Result |
|---|---|---|
| 27B MLX model | `lms ps`: `ternary-bonsai-27b-mlx`, context 41,472 | loaded, but ordinary OpenAI-compatible requests fail |
| 27B GGUF + mmproj | `~/.lmstudio/models/prism-ml/Ternary-Bonsai-27B-gguf/` | files present; model load fails before health check |
| Local embeddings | Nomic embedding model appears in `/v1/models` | fails: Bionic references missing packaged `embeddingworker.js` |
| Local API | `lms server start --bind 127.0.0.1 -p 1234` | working local-only server and model listing |

## Exact failure modes

1. **Embedding worker package path.** `/v1/embeddings` returns a missing
   `.../.webpack-bionic/lib/embeddingworker.js` error. Do not call this a semantic RAG
   system until that endpoint succeeds.
2. **Tool grammar leaked into API requests.** The MLX model originally rejected an ordinary first
   token because the runtime constrains it to Bionic function-call XML. This is visible
   in the server log and makes generic `chat/completions`, `completions`, and `lms chat`
   unusable. A brand-new Bionic session reproduced the same error, so it is not caused
   by the earlier Researcher session or attached documents.
   Supplying an explicit OpenAI-compatible `tools: []` and `tool_choice: "none"` still
   produced the same forced grammar. The local MLX backend was applying its Qwen 3.5
   llguidance guard whenever Bionic-rendered tool declarations appeared in the prompt,
   regardless of the request's empty tools array. The local recovery disables that guard
   by default (it can be explicitly re-enabled with `LMS_ENABLE_QWEN35_TOOL_GUARD=1`) and
   uses a raw Qwen completion prompt with a closed `<think>` block for Bonsai Agent's
   non-tool RAG calls. Both the formerly failing exact completion and cited civic RAG
   synthesis now succeed. This does not prove Bionic's interactive tool-workspace flow;
   it proves the 27B text backend is usable for the local agent.
3. **GGUF runtime does not reach healthy.** `lms load ternary-bonsai-27b` selected the
   local llama-server runtime and exited before its health check. Bionic's own
   llama-server reports `token_embd.weight has invalid ggml type 42`; this runtime does
   not recognize the model's custom Dspark GGML type. The downloaded GGUF and mmproj
   SHA-256 values match LM Studio's manifest, so this is not evidence of a corrupt model.
   A stock llama.cpp probe instead reports `dspark.fc.weight has offset 337718592,
   expected 357584192`, which is a second symptom of the same missing PrismML runtime
   support. The valid model needs PrismML's patched llama.cpp runtime; the agent does not
   retry in a loop or replace Bionic configuration automatically.
4. **The separate Bonsai Image demo initially selected an unavailable remote decoder.**
   Its ternary MLX weights and pipeline initialized successfully, but the local pipeline
   was hard-coded to use FLUX.2's small decoder through `hf_hub_download`.
   `~/.cache/huggingface` is a symlink to the currently absent
   `/Volumes/T7/AI/huggingface-cache`, so that original path failed with
   `FileNotFoundError`. The checkpoint already includes `vae/diffusion_pytorch_model.safetensors`.
   The local pipeline now selects that bundled full VAE instead. A 512×512 two-step PNG
   was verified with `HF_HUB_OFFLINE=1`; this image capability is now exposed through
   Bonsai Agent, without treating Bionic as an image generator.

## Design consequence

`bonsai_agent.py` mirrors the useful local architecture—project sources, retrieval,
cited synthesis, optional image input—but has a dependency-free retrieval fallback. It
never manufactures an answer if the local model is unavailable. It now uses the repaired
27B completion route for text synthesis; Bionic's packaged embeddings and interactive
tool adapter remain separate repair targets. A local image-understanding probe currently
returns no final vision answer after spending its budget in reasoning, so image analysis
is deliberately not presented as working. The persisted source/citation contract is
unchanged.
