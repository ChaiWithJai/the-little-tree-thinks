#!/usr/bin/env python3
"""Bonsai Agent: private, local project retrieval with optional LM Studio synthesis.

The index never leaves this machine.  Its default retrieval is deliberately dependency-
free (BM25-like lexical scoring) so a broken embedding worker cannot make private notes
unsearchable.  When LM Studio's embedding/generation APIs are healthy, the same CLI uses
them as an enhancement, never as an uncited source of truth.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import os
import re
import subprocess
import sys
import time
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = Path(os.getenv("BONSAI_AGENT_CONFIG", ROOT / "bonsai_agent.config.json")).expanduser()
EXAMPLE_CONFIG_PATH = ROOT / "bonsai_agent.config.example.json"
STATE_DIR = Path(os.getenv("BONSAI_STATE_DIR", ROOT / ".bonsai-agent")).expanduser()
INDEX_PATH = STATE_DIR / "index.json"
IMAGE_DIR = STATE_DIR / "images"
HTML_DIR = STATE_DIR / "pages"
TEXT_EXTENSIONS = {".md", ".txt", ".rst", ".json", ".yaml", ".yml", ".html", ".htm", ".csv"}
IGNORE_DIRS = {".git", ".agents", ".codex", ".cursor", ".claude", "node_modules", "dist", "build", "target", "output", "public", "artifacts", ".astro", ".next", ".cache", ".venv", "venv", "coverage", "test-results", ".playwright-cli"}
MAX_FILES_PER_ROOT = 350
PREVIEW_BASE_CSS = """
<style id="bonsai-preview-base">
:root{color-scheme:light;--ink:#1f2a22;--leaf:#315b42;--leaf-2:#47795a;--cream:#f7f2e7;--paper:#fffdf8;--line:#dcd5c7;--muted:#687169}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--cream);color:var(--ink);font:16px/1.55 ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:inherit}button,.btn{font:inherit;cursor:pointer}.container{width:min(1120px,calc(100% - 40px));margin-inline:auto}.navbar,nav{background:var(--leaf);color:white}.navbar .container,nav .container{min-height:68px;display:flex;align-items:center;justify-content:space-between;gap:24px}.logo{font-weight:800;text-decoration:none}.nav-links,nav ul{display:flex;gap:24px;list-style:none;margin:0;padding:0}.nav-links a,nav a{text-decoration:none}.hero,main{padding:clamp(72px,10vw,132px) 0;text-align:center;background:linear-gradient(145deg,var(--paper),#e8efdf)}.hero-title,h1{max-width:800px;margin:0 auto 18px;font:700 clamp(42px,7vw,76px)/1.02 Georgia,serif;letter-spacing:-.04em}.hero-subtitle{max-width:650px;margin:0 auto 30px;color:var(--muted);font-size:clamp(17px,2vw,21px)}.hero-buttons{display:flex;justify-content:center;gap:12px;flex-wrap:wrap}section{padding:76px 0}.section-title,h2{text-align:center;font:700 clamp(30px,4vw,44px)/1.1 Georgia,serif}.feature-grid,.pricing-grid,[class$="-grid"]{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}.feature-card,.pricing-card,[class$="-card"]{padding:28px;border:1px solid var(--line);border-radius:18px;background:var(--paper);box-shadow:0 12px 35px rgba(39,55,43,.08);transition:transform .2s,box-shadow .2s}.feature-icon{font-size:34px}.btn{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:10px 18px;border:1px solid currentColor;border-radius:999px;background:transparent;color:inherit;font-weight:750}.btn-primary{border-color:var(--leaf);background:var(--leaf);color:white}.btn-outline{border-color:currentColor}.price{font-size:38px;font-weight:800}.pricing-list{padding-left:20px}.featured{outline:3px solid var(--leaf-2)}footer,.footer{padding:32px 0;background:#20392a;color:white;text-align:center}
@media(max-width:720px){.nav-links,nav ul{display:none}.feature-grid,.pricing-grid,[class$="-grid"]{grid-template-columns:1fr}.container{width:min(100% - 28px,1120px)}section{padding:52px 0}.hero,main{padding:72px 0}.navbar .container,nav .container{min-height:58px}}
</style>
""".strip()


def ensure_preview_styles(html: str) -> str:
    """Guarantee a readable responsive baseline; model-authored CSS can override it."""
    if 'id="bonsai-preview-base"' in html:
        return html
    if "</head>" in html.lower():
        position = html.lower().index("</head>")
        return html[:position] + PREVIEW_BASE_CSS + html[position:]
    return PREVIEW_BASE_CSS + html


def finalize_generated_html(prefix: str, continuation: str, *, bounded: bool = False) -> str:
    """Turn a complete or deadline-clipped stream into a valid preview document."""
    html = prefix + continuation
    html = re.sub(r"```(?:html)?|```", "", html, flags=re.IGNORECASE).strip()
    end = html.lower().rfind("</html>")
    if end >= 0:
        html = html[:end + len("</html>")]
    if html.lower().count("<style") > html.lower().count("</style>"):
        html += "</style>"
    if html.lower().count("<script") > html.lower().count("</script>"):
        html += "</script>"
    if "</body>" not in html.lower():
        html += "</body>"
    if "</html>" not in html.lower():
        html += "</html>"
    if bounded:
        html = html.replace("</body>", "<!-- generation finalized at the local deadline --></body>", 1)
    return ensure_preview_styles(html)


def config() -> dict[str, Any]:
    source = CONFIG_PATH if CONFIG_PATH.exists() else EXAMPLE_CONFIG_PATH
    value = json.loads(source.read_text())
    overrides = {
        ("lm_studio", "base_url"): os.getenv("BONSAI_TEXT_BASE_URL"),
        ("lm_studio", "chat_model"): os.getenv("BONSAI_TEXT_MODEL"),
        ("lm_studio", "embedding_model"): os.getenv("BONSAI_EMBEDDING_MODEL"),
        ("html", "base_url"): os.getenv("BONSAI_HTML_BASE_URL"),
        ("html", "model"): os.getenv("BONSAI_HTML_MODEL"),
        ("image", "demo_dir"): os.getenv("BONSAI_IMAGE_DEMO_DIR"),
    }
    for (section, key), override in overrides.items():
        if override:
            value.setdefault(section, {})[key] = override
    return value


def configured_corpora() -> list[str]:
    corpora = config().get("corpora", {})
    if not isinstance(corpora, dict):
        raise ValueError("The config corpora value must be an object.")
    return sorted(str(name) for name in corpora)


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'_-]{1,}", text.lower())


def source_files(roots: list[str]):
    for raw_root in roots:
        root = Path(raw_root).expanduser()
        if not root.exists():
            print(f"warn: source root not found: {root}", file=sys.stderr)
            continue
        yielded = 0
        for directory, children, files in os.walk(root):
            children[:] = [child for child in children if child not in IGNORE_DIRS and not child.startswith((".venv", "dist ", "output ")) and child != "site-packages"]
            for name in files:
                path = Path(directory) / name
                if path.suffix.lower() not in TEXT_EXTENSIONS:
                    continue
                try:
                    if path.stat().st_size <= 1_500_000:
                        yield path
                        yielded += 1
                        if yielded >= MAX_FILES_PER_ROOT:
                            print(f"warn: capped {root} at {MAX_FILES_PER_ROOT} files; add a narrower root for more coverage", file=sys.stderr)
                            break
                except OSError:
                    pass
            if yielded >= MAX_FILES_PER_ROOT:
                break


def chunk_text(text: str, size: int = 1200, overlap: int = 180) -> list[str]:
    text = re.sub(r"\r\n?", "\n", text).strip()
    chunks, start = [], 0
    while start < len(text):
        end = min(len(text), start + size)
        if end < len(text):
            break_at = max(text.rfind("\n", start + size - 250, end), text.rfind(". ", start + size - 250, end))
            if break_at > start:
                end = break_at + 1
        part = text[start:end].strip()
        if len(part) >= 80:
            chunks.append(part)
        start = max(end, start + 1) - overlap if end < len(text) else len(text)
    return chunks


def build_index(corpora: list[str], reset: bool) -> dict[str, Any]:
    cfg = config()
    unknown = set(corpora) - set(cfg.get("corpora", {}))
    if unknown:
        raise ValueError(f"Unknown corpus: {sorted(unknown)[0]}.")
    selected = {name: cfg["corpora"][name] for name in corpora}
    docs = []
    for corpus, roots in selected.items():
        for file in source_files(roots):
            try:
                text = file.read_text(errors="ignore")
            except OSError:
                continue
            for number, chunk in enumerate(chunk_text(text)):
                docs.append({"id": f"{corpus}:{file}:{number}", "corpus": corpus, "path": str(file), "chunk": number, "text": chunk, "terms": Counter(tokenize(chunk))})
    df = Counter()
    for doc in docs:
        df.update(doc["terms"].keys())
        doc["terms"] = dict(doc["terms"])
    result = {"version": 1, "built_at": time.time(), "documents": docs, "document_frequency": dict(df), "corpora": corpora}
    STATE_DIR.mkdir(exist_ok=True)
    INDEX_PATH.write_text(json.dumps(result, ensure_ascii=False))
    return result


def load_index() -> dict[str, Any]:
    if not INDEX_PATH.exists():
        raise SystemExit("No index exists. Configure a source and run: python3 bonsai_agent.py index")
    return json.loads(INDEX_PATH.read_text())


def search(query: str, limit: int, corpus: str | None = None) -> list[dict[str, Any]]:
    index = load_index(); terms = tokenize(query); total = len(index["documents"])
    hits = []
    for doc in index["documents"]:
        if corpus and doc["corpus"] != corpus:
            continue
        length = sum(doc["terms"].values()) or 1; score = 0.0
        for term in terms:
            tf = doc["terms"].get(term, 0)
            if tf:
                idf = math.log((total + 1) / (index["document_frequency"].get(term, 0) + 1)) + 1
                score += (tf / length) * idf
        if score:
            hits.append({**doc, "score": round(score, 5)})
    return sorted(hits, key=lambda hit: hit["score"], reverse=True)[:limit]


def api_status() -> dict[str, Any]:
    base = config()["lm_studio"]["base_url"].rstrip("/")
    try:
        response = requests.get(f"{base}/models", timeout=4)
        response.raise_for_status()
        models = response.json().get("data", [])
        return {"reachable": True, "base_url": base, "models": [m.get("id") for m in models]}
    except Exception as error:
        return {"reachable": False, "base_url": base, "error": str(error)}


def html_status() -> dict[str, Any]:
    html_cfg = config().get("html", {})
    base = str(html_cfg.get("base_url", "")).rstrip("/")
    model = html_cfg.get("model")
    if not base or not model:
        return {"ready": False, "error": "No HTML runtime is configured."}
    try:
        response = requests.get(f"{base}/models", timeout=4)
        response.raise_for_status()
        models = [item.get("id") or item.get("name") for item in response.json().get("data", response.json().get("models", []))]
        return {"ready": model in models, "base_url": base, "model": model, "models": models}
    except Exception as error:
        return {"ready": False, "base_url": base, "model": model, "error": str(error)}


def embedding_status() -> dict[str, Any]:
    """Probe the configured embedding route instead of trusting model discovery."""
    cfg = config()["lm_studio"]
    model = cfg.get("embedding_model")
    base = cfg["base_url"].rstrip("/")
    if not model:
        return {"configured": False, "ready": False, "error": "No embedding model is configured."}
    try:
        response = requests.post(f"{base}/embeddings", json={"model": model, "input": "runtime health probe"}, timeout=12)
        response.raise_for_status()
        data = response.json().get("data", [])
        dimensions = len(data[0].get("embedding", [])) if data else 0
        if not dimensions:
            raise RuntimeError("Embedding endpoint returned no vector.")
        return {"configured": True, "ready": True, "model": model, "dimensions": dimensions}
    except Exception as error:
        detail = str(error)
        try:
            body = response.json()  # type: ignore[possibly-undefined]
            detail = body.get("error", detail)
        except Exception:
            pass
        return {"configured": True, "ready": False, "model": model, "error": detail}


def image_status() -> dict[str, Any]:
    """Report only the explicitly configured, local Bonsai Image runtime."""
    image_cfg = config().get("image", {})
    demo = Path(image_cfg.get("demo_dir", "")).expanduser()
    runner = demo / ".venv" / "bin" / "python"
    script = demo / "scripts" / "generate.py"
    model = demo / "models" / "bonsai-image-4B-ternary-mlx"
    pipeline = demo / "vendor" / "image-studio" / "backend" / "pipeline.py"
    ready = all(path.exists() for path in (runner, script, model, pipeline))
    return {"ready": ready, "demo_dir": str(demo), "model": image_cfg.get("model", "ternary-mlx"),
            "pipeline_uses_bundled_vae": 'vae_variant="full"' in pipeline.read_text(errors="ignore") if pipeline.exists() else False}


def generate_image(prompt: str, *, seed: int | None = None, steps: int | None = None, size: str | None = None) -> dict[str, Any]:
    """Render with the discovered local demo. No network access is allowed."""
    if not prompt.strip():
        raise ValueError("Enter an image prompt.")
    if len(prompt) > 1_500:
        raise ValueError("Image prompt must be at most 1,500 characters.")
    image_cfg = config().get("image", {})
    state = image_status()
    if not state["ready"] or not state["pipeline_uses_bundled_vae"]:
        raise RuntimeError("The local Bonsai Image runtime is not ready.")
    chosen_steps = int(steps if steps is not None else image_cfg.get("default_steps", 2))
    if not 2 <= chosen_steps <= 8:
        raise ValueError("Image steps must be between 2 and 8.")
    chosen_size = size or image_cfg.get("default_size", "512x512")
    if chosen_size not in {"512x512", "624x416", "416x624", "704x352", "352x704"}:
        raise ValueError("Unsupported image size.")
    chosen_seed = int(seed) if seed is not None else int.from_bytes(os.urandom(4), "big")
    if not 0 <= chosen_seed <= 4_294_967_295:
        raise ValueError("Seed must be a non-negative 32-bit integer.")
    demo = Path(image_cfg["demo_dir"]).expanduser()
    output_name = f"bonsai-{int(time.time())}-{uuid.uuid4().hex[:8]}.png"
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    output = IMAGE_DIR / output_name
    command = [str(demo / ".venv" / "bin" / "python"), str(demo / "scripts" / "generate.py"),
               "--model", str(image_cfg.get("model", "ternary-mlx")), "--prompt", prompt,
               "--seed", str(chosen_seed), "--steps", str(chosen_steps), "--size", chosen_size,
               "--output", str(output)]
    environment = {**os.environ, "HF_HUB_OFFLINE": "1"}
    try:
        completed = subprocess.run(command, cwd=demo, env=environment, text=True,
                                   capture_output=True, timeout=180, check=False)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Local image render exceeded 180 seconds.") from error
    if completed.returncode != 0 or not output.exists() or output.stat().st_size < 100:
        output.unlink(missing_ok=True)
        trace = (completed.stderr or completed.stdout).strip()[-1200:]
        raise RuntimeError(f"Local image render failed: {trace or 'no diagnostic output'}")
    return {"filename": output_name, "url": f"/generated/{output_name}", "seed": chosen_seed,
            "steps": chosen_steps, "size": chosen_size, "prompt": prompt}


def synthesize(question: str, hits: list[dict[str, Any]], image: Path | None = None) -> tuple[str | None, str | None]:
    cfg = config(); base = cfg["lm_studio"]["base_url"].rstrip("/")
    context = "\n\n".join(f"[S{n}] {h['path']}\n{h['text']}" for n, h in enumerate(hits, 1))
    instruction = ("Answer only from the supplied sources. Cite claims as [S1], [S2]. "
                   "If the sources do not establish an answer, say so. Give the answer directly; do not describe your reasoning.\n\n" + context + f"\n\nQuestion: {question}")
    # Ternary Bonsai is a Qwen reasoning model.  Bionic's chat endpoint injects
    # workspace tools and starts its thinking channel even for tools: [].  A
    # local completions prompt with a closed thinking block is the verified
    # non-tool/RAG route and returns ordinary cited text.
    if image is None:
        prompt = ("<|im_start|>system\nYou are a careful private research assistant.\n<|im_end|>\n"
                  f"<|im_start|>user\n{instruction}<|im_end|>\n"
                  "<|im_start|>assistant\n<think>\n\n</think>\n\n")
        payload = {"model": cfg["lm_studio"]["chat_model"], "prompt": prompt,
                   "temperature": 0.1, "max_tokens": 500}
        try:
            response = requests.post(f"{base}/completions", json=payload, timeout=150)
            response.raise_for_status()
            text = response.json()["choices"][0]["text"].strip()
            return (text or None), None if text else "Model returned an empty completion."
        except Exception as error:
            return None, str(error)
    content: Any = instruction
    encoded = base64.b64encode(image.read_bytes()).decode()
    content = [{"type": "text", "text": instruction}, {"type": "image_url", "image_url": {"url": f"data:image/{image.suffix.lstrip('.')};base64,{encoded}"}}]
    payload = {"model": cfg["lm_studio"]["chat_model"], "messages": [{"role": "user", "content": content}], "temperature": 0.1, "max_tokens": 700}
    try:
        response = requests.post(f"{base}/chat/completions", json=payload, timeout=150)
        response.raise_for_status()
        answer = (response.json()["choices"][0]["message"].get("content") or "").strip()
        return (answer or None), None if answer else "Local vision chat returned no final answer (reasoning budget exhausted)."
    except Exception as error:
        return None, str(error)


def generate_html(prompt: str) -> dict[str, Any]:
    """Generate one bounded, self-contained HTML document for sandboxed preview."""
    prompt = str(prompt or "").strip()
    if not prompt:
        raise ValueError("Describe the HTML page to build.")
    if len(prompt) > 8_000:
        raise ValueError("HTML requests must be at most 8,000 characters.")
    cfg = config(); html_cfg = cfg.get("html", {}); base = html_cfg.get("base_url", cfg["lm_studio"]["base_url"]).rstrip("/")
    model = html_cfg.get("model", cfg["lm_studio"]["chat_model"])
    timeout_seconds = int(html_cfg.get("timeout_seconds", 40))
    max_tokens = int(html_cfg.get("max_tokens", 1000))
    instruction = (
        "Continue the already-open HTML body with the requested interface in under 1,400 output tokens. "
        "Write semantic page markup first, then one compact embedded style block, and vanilla JavaScript only when interaction is required. "
        "Do not use external URLs, packages, fonts, images, markdown fences, explanations, or placeholders. "
        "Make it responsive and accessible. End with </body></html>; do not repeat the doctype, html, head, or body opening tags.\n\n"
        f"REQUEST:\n{prompt}"
    )
    prefix = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Generated page</title></head><body>'
    )
    model_prompt = (
        "<|im_start|>system\nYou are a senior frontend engineer. Output only finished HTML.\n<|im_end|>\n"
        f"<|im_start|>user\n{instruction}<|im_end|>\n"
        f"<|im_start|>assistant\n<think>\n\n</think>\n\n{prefix}"
    )
    payload = {"model": model, "prompt": model_prompt, "temperature": 0.2, "max_tokens": max_tokens, "stream": True}
    parts: list[str] = []
    bounded = False
    response = None
    started = time.monotonic()
    first_token_ms = None
    stream_chunks = 0
    finish_reason = None
    try:
        response = requests.post(f"{base}/completions", json=payload, stream=True, timeout=(5, timeout_seconds + 5))
        response.raise_for_status()
        for raw_line in response.iter_lines(decode_unicode=True):
            if time.monotonic() - started >= timeout_seconds:
                bounded = True
                break
            if not raw_line or not raw_line.startswith("data: "):
                continue
            data = raw_line.removeprefix("data: ")
            if data == "[DONE]":
                break
            event = json.loads(data)
            choice = event.get("choices", [{}])[0]
            text = choice.get("text", "")
            if text and first_token_ms is None:
                first_token_ms = round((time.monotonic() - started) * 1000)
            if text:
                stream_chunks += 1
                parts.append(text)
            finish_reason = choice.get("finish_reason") or finish_reason
    except requests.Timeout as error:
        if not parts:
            raise RuntimeError(f"HTML generation produced no output within the {timeout_seconds}-second limit. Try again.") from error
        bounded = True
    except Exception as error:
        raise RuntimeError(f"Local HTML generation failed: {error}") from error
    finally:
        if response is not None:
            response.close()
    continuation = "".join(parts)
    if not continuation.strip():
        raise RuntimeError("The local HTML model returned no page content. Try again.")
    html = finalize_generated_html(prefix, continuation, bounded=bounded)
    return {"html": html, "telemetry": {
        "model": model, "first_token_ms": first_token_ms, "generation_ms": round((time.monotonic() - started) * 1000),
        "stream_chunks": stream_chunks, "output_chars": len(continuation), "bounded": bounded,
        "finish_reason": finish_reason or ("deadline" if bounded else "stop"), "max_tokens": max_tokens,
    }}


def print_hits(hits: list[dict[str, Any]]):
    for n, hit in enumerate(hits, 1):
        print(f"[S{n}] {hit['corpus']} · {hit['path']}#{hit['chunk']} · score={hit['score']}")
        print(hit["text"][:700].replace("\n", " ") + ("…" if len(hit["text"]) > 700 else ""))
        print()


def main() -> None:
    corpora = configured_corpora()
    parser = argparse.ArgumentParser(description="Private local retrieval and generation workbench")
    sub = parser.add_subparsers(dest="command", required=True)
    p_index = sub.add_parser("index"); p_index.add_argument("--corpus", nargs="+", choices=corpora or None, default=corpora); p_index.add_argument("--reset", action="store_true")
    p_search = sub.add_parser("search"); p_search.add_argument("question"); p_search.add_argument("--corpus", choices=corpora or None); p_search.add_argument("-k", type=int, default=6)
    p_ask = sub.add_parser("ask"); p_ask.add_argument("question"); p_ask.add_argument("--corpus", choices=corpora or None); p_ask.add_argument("--image", type=Path); p_ask.add_argument("-k", type=int, default=6); p_ask.add_argument("--no-model", action="store_true")
    p_image = sub.add_parser("image"); p_image.add_argument("prompt"); p_image.add_argument("--seed", type=int); p_image.add_argument("--steps", type=int); p_image.add_argument("--size")
    sub.add_parser("status")
    args = parser.parse_args()
    if args.command == "index":
        if not args.corpus:
            raise SystemExit("No corpora are configured. Add one to bonsai_agent.config.json first.")
        index = build_index(args.corpus, args.reset); counts = Counter(d["corpus"] for d in index["documents"])
        print(json.dumps({"indexed_chunks": len(index["documents"]), "by_corpus": counts, "index": str(INDEX_PATH)}, indent=2, default=dict)); return
    if args.command == "status":
        output = {"lm_studio": api_status(), "image": image_status(), "index": None}
        if INDEX_PATH.exists():
            index = load_index(); output["index"] = {"chunks": len(index["documents"]), "corpora": index["corpora"], "built_at": index["built_at"]}
        print(json.dumps(output, indent=2)); return
    if args.command == "image":
        print(json.dumps(generate_image(args.prompt, seed=args.seed, steps=args.steps, size=args.size), indent=2)); return
    hits = search(args.question, args.k, getattr(args, "corpus", None))
    if args.command == "search":
        print_hits(hits); return
    if not hits:
        raise SystemExit("No relevant local sources found; refine the question or index more sources.")
    if args.no_model:
        print_hits(hits); return
    answer, error = synthesize(args.question, hits, args.image)
    if answer:
        print(answer + "\n\nSources:\n"); print_hits(hits); return
    print("MODEL UNAVAILABLE — returning a cited retrieval dossier rather than an invented answer.", file=sys.stderr)
    print(f"LM Studio error: {error}", file=sys.stderr); print_hits(hits)


if __name__ == "__main__":
    main()
