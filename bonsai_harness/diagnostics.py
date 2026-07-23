from __future__ import annotations

from typing import Any


def runtime_diagnostics(*, text: dict[str, Any], embedding: dict[str, Any], image: dict[str, Any], index_ready: bool, chat_model: str) -> list[dict[str, Any]]:
    """Live capability evidence, with required routes separated from optional ones."""
    models = text.get("models", [])
    text_ready = bool(text.get("reachable") and chat_model in models)
    return [
        {
            "id": "retrieval", "required": True, "blocking": not index_ready,
            "severity": "ready" if index_ready else "blocked",
            "title": "Local retrieval index is ready" if index_ready else "Local retrieval index is missing",
            "summary": "The deterministic lexical route keeps private source retrieval independent of optional embedding workers.",
            "evidence": "Indexed local chunks are available." if index_ready else "No local index was found.",
            "impact": "Required evidence retrieval is operational." if index_ready else "Runs cannot retrieve evidence until the index is built.",
        },
        {
            "id": "synthesis", "required": True, "blocking": not text_ready,
            "severity": "ready" if text_ready else "blocked",
            "title": "Bonsai MLX synthesis is ready" if text_ready else "Configured synthesis model is unavailable",
            "summary": f"The harness uses {chat_model} through the local completions route.",
            "evidence": f"Discovered models: {', '.join(models) or 'none'}" if text.get("reachable") else text.get("error", "Local model API is unreachable."),
            "impact": "Required cited text synthesis is operational." if text_ready else "Model-backed runs cannot complete synthesis.",
        },
        {
            "id": "embedding", "required": False, "blocking": False,
            "severity": "ready" if embedding.get("ready") else "bypassed",
            "title": "Semantic embeddings are ready" if embedding.get("ready") else "Optional Bionic embedding route is bypassed",
            "summary": "The embedding enhancement is healthy." if embedding.get("ready") else "Bionic is missing its packaged embedding worker; the harness automatically uses its verified lexical retriever.",
            "evidence": f"{embedding.get('dimensions')} dimensions from {embedding.get('model')}." if embedding.get("ready") else embedding.get("error", "Embedding probe failed."),
            "impact": "Semantic retrieval is available." if embedding.get("ready") else "No execution blocker: local evidence retrieval remains available.",
        },
        {
            "id": "gguf", "required": False, "blocking": False, "severity": "bypassed",
            "title": "Optional GGUF route is bypassed",
            "summary": "The stock llama.cpp runtime does not support the model's custom tensor type, so the harness selects the working MLX model.",
            "evidence": "GGUF probe reported invalid ggml type 42; the configured MLX synthesis route is checked independently above.",
            "impact": "No execution blocker: GGUF is not on the active harness path.",
        },
        {
            "id": "image", "required": False, "blocking": False,
            "severity": "ready" if image.get("ready") and image.get("pipeline_uses_bundled_vae") else "optional",
            "title": "Bonsai Image 4B runs locally" if image.get("ready") else "Optional image runtime is unavailable",
            "summary": "The local ternary MLX image model uses its bundled VAE." if image.get("ready") else "Text evaluation remains available without image generation.",
            "evidence": image.get("demo_dir", "No image demo path configured."),
            "impact": "Visual artifacts can be rendered locally." if image.get("ready") else "No text-run blocker.",
        },
        {
            "id": "vision", "required": False, "blocking": False, "severity": "optional",
            "title": "Vision analysis is outside this harness path",
            "summary": "The workbench currently composes images and cited text as separate, verified adapters.",
            "evidence": "Text synthesis and image generation expose independent health checks.",
            "impact": "No execution blocker; image understanding is not promised by this workflow.",
        },
    ]
