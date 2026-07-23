#!/usr/bin/env python3
"""Local Bonsai evaluation API and static UI."""
from __future__ import annotations

import json
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import bonsai_agent as agent
from bonsai_harness.adapters import BonsaiAgentAdapter
from bonsai_harness.catalog import CaseCatalog
from bonsai_harness.config import HarnessSettings
from bonsai_harness.coordinator import RunCoordinator
from bonsai_harness.html_service import HtmlGenerationService
from bonsai_harness.repository import SQLiteRunRepository
from bonsai_harness.service import EvaluationService
from bonsai_harness.tracing import LocalTraceStore

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
SETTINGS = HarnessSettings.from_env(ROOT)
CATALOG = CaseCatalog(SETTINGS.case_catalog_path)
PAGE_PRESETS_PATH = ROOT / "evals" / "page-presets.json"
REPOSITORY = SQLiteRunRepository(SETTINGS.database_path, SETTINGS.legacy_runs_path)
TRACE_STORE = LocalTraceStore(SETTINGS.database_path)


def catalog_payload() -> dict:
    return CATALOG.load()


def evaluation_service() -> EvaluationService:
    policy = catalog_payload()
    return EvaluationService(
        BonsaiAgentAdapter(agent),
        REPOSITORY,
        retrieval_limit=SETTINGS.retrieval_limit,
        history_limit=SETTINGS.history_limit,
        allowed_issues={item["id"] for item in policy["review_issues"]},
    )


def html_service() -> HtmlGenerationService:
    html_cfg = agent.config()["html"]
    return HtmlGenerationService(
        agent.generate_html, REPOSITORY, agent.HTML_DIR,
        html_cfg["model"], html_cfg.get("timeout_seconds", 40),
    )


COORDINATOR = RunCoordinator(evaluation_service, repository=REPOSITORY, trace_store=TRACE_STORE, max_concurrent=SETTINGS.max_concurrent_runs)
HTML_COORDINATOR = RunCoordinator(html_service, repository=REPOSITORY, trace_store=TRACE_STORE, max_concurrent=SETTINGS.max_concurrent_runs)


def json_response(handler: BaseHTTPRequestHandler, body: object, status: int = 200, *, cache_control: str = "no-store") -> None:
    data = json.dumps(body, ensure_ascii=False).encode()
    etag = f'"{hashlib.sha256(data).hexdigest()[:24]}"' if cache_control != "no-store" else None
    if etag and handler.headers.get("If-None-Match") == etag:
        handler.send_response(304)
        handler.send_header("Cache-Control", cache_control)
        handler.send_header("ETag", etag)
        handler.end_headers()
        return
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", cache_control)
    if etag:
        handler.send_header("ETag", etag)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


class App(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def serve_file(self, file: Path, content_type: str, *, cache_control: str = "no-cache") -> None:
        data = file.read_bytes()
        etag = f'"{hashlib.sha256(data).hexdigest()[:24]}"'
        if self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self.send_header("Cache-Control", cache_control)
            self.send_header("ETag", etag)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", cache_control)
        self.send_header("ETag", etag)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        is_app_route = parsed.path == "/" or any(
            parsed.path == prefix or parsed.path.startswith(prefix + "/")
            for prefix in ("/draft", "/jobs", "/runs")
        )
        if is_app_route:
            return self.serve_file(WEB / "index.html", "text/html; charset=utf-8")
        if parsed.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if parsed.path == "/app.js":
            return self.serve_file(WEB / "app.js", "text/javascript; charset=utf-8")
        if parsed.path == "/fsm.js":
            return self.serve_file(WEB / "fsm.js", "text/javascript; charset=utf-8")
        if parsed.path == "/styles.css":
            return self.serve_file(WEB / "styles.css", "text/css; charset=utf-8")
        if parsed.path == "/api/status":
            index = None
            if agent.INDEX_PATH.exists():
                loaded = agent.load_index()
                index = {"chunks": len(loaded["documents"]), "corpora": loaded["corpora"], "built_at": loaded["built_at"]}
            text_status = agent.api_status()
            html_status = agent.html_status()
            image_status = agent.image_status()
            configured = agent.config()
            configured_corpora = sorted(configured.get("corpora", {}))
            indexed_corpora = index.get("corpora", []) if index else []
            available_corpora = sorted(set(configured_corpora) | set(indexed_corpora))
            chat_model = configured["lm_studio"]["chat_model"]
            text_ready = bool(text_status.get("reachable") and chat_model in text_status.get("models", []))
            harness_ready = bool(html_status.get("ready") or (index is not None and text_ready))
            return json_response(self, {
                "lm_studio": text_status,
                "image": image_status,
                "html": html_status,
                "index": index,
                "harness": {
                    "ready": harness_ready,
                    "repository": "sqlite",
                    "retrieval_limit": SETTINGS.retrieval_limit,
                    "history_limit": SETTINGS.history_limit,
                    "max_concurrent_runs": SETTINGS.max_concurrent_runs,
                    "schema_version": 1,
                    "corpora": [
                        {"id": name, "label": name.replace("_", " ").replace("-", " ").title()}
                        for name in available_corpora
                    ],
                    "pipeline": [
                        {"id": "case", "label": "Define a checkable case"},
                        {"id": "retrieval", "label": "Retrieve local evidence"},
                        {"id": "synthesis", "label": "Synthesize with the selected model"},
                        {"id": "citations", "label": "Resolve cited source IDs"},
                        {"id": "checkpoint", "label": "Checkpoint the inspectable artifact"},
                        {"id": "review", "label": "Apply and retain human judgment"},
                    ],
                    "adapters": [
                        {"id": "retrieval", "name": "lexical-retriever", "status": "ready" if index else "unavailable", "role": "local corpus search"},
                        {"id": "synthesis", "name": chat_model, "status": "ready" if text_ready else "unavailable", "role": "cited text synthesis"},
                        {"id": "html", "name": html_status.get("model", "html-generator"), "status": "ready" if html_status.get("ready") else "unavailable", "role": "bounded HTML page generation"},
                        {"id": "citations", "name": "citation-checker", "status": "ready", "role": "deterministic source validation"},
                        {"id": "image", "name": configured.get("image", {}).get("model", "bonsai-image"), "status": "ready" if image_status.get("ready") else "unavailable", "role": "offline visual artifacts"},
                    ],
                },
            })
        if parsed.path == "/api/cases":
            return json_response(self, catalog_payload(), cache_control="private, max-age=60, stale-while-revalidate=300")
        if parsed.path == "/api/page-presets":
            return json_response(self, json.loads(PAGE_PRESETS_PATH.read_text()), cache_control="private, max-age=60, stale-while-revalidate=300")
        if parsed.path == "/api/runs":
            return json_response(self, {"runs": evaluation_service().recent()})
        if parsed.path.startswith("/api/runs/"):
            run_id = parsed.path.removeprefix("/api/runs/")
            run = REPOSITORY.get(run_id) if run_id and "/" not in run_id else None
            return json_response(self, {"run": run}) if run else json_response(self, {"error": "Run not found."}, 404)
        if parsed.path == "/api/traces":
            values = parse_qs(parsed.query)
            return json_response(self, {"traces": TRACE_STORE.recent(values.get("limit", [50])[0], values.get("kind", [None])[0])})
        if parsed.path == "/api/benchmarks/summary":
            values = parse_qs(parsed.query)
            return json_response(self, TRACE_STORE.summary(values.get("limit", [200])[0]))
        if parsed.path.startswith("/api/jobs/"):
            try:
                return json_response(self, {"job": COORDINATOR.get(parsed.path.removeprefix("/api/jobs/"))})
            except KeyError:
                return json_response(self, {"error": "Job not found."}, 404)
        if parsed.path == "/api/search":
            values = parse_qs(parsed.query)
            question = values.get("q", [""])[0].strip()
            corpus = values.get("corpus", [None])[0]
            limit = min(int(values.get("k", [SETTINGS.retrieval_limit])[0]), 10)
            if not question:
                return json_response(self, {"error": "Enter a question."}, 400)
            return json_response(self, {"hits": agent.search(question, limit, corpus)})
        if parsed.path.startswith("/generated/"):
            name = Path(parsed.path).name
            if name != parsed.path.removeprefix("/generated/") or not name.endswith(".png"):
                return json_response(self, {"error": "Not found"}, 404)
            image = agent.IMAGE_DIR / name
            return self.serve_file(image, "image/png", cache_control="private, max-age=31536000, immutable") if image.exists() else json_response(self, {"error": "Not found"}, 404)
        if parsed.path.startswith("/previews/"):
            name = Path(parsed.path).name
            if name != parsed.path.removeprefix("/previews/") or not name.endswith(".html"):
                return json_response(self, {"error": "Not found"}, 404)
            preview = agent.HTML_DIR / name
            if not preview.exists():
                return json_response(self, {"error": "Not found"}, 404)
            data = preview.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "private, max-age=31536000, immutable")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; font-src data:")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers(); self.wfile.write(data); return
        return json_response(self, {"error": "Not found"}, 404)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            if self.path == "/api/image":
                prompt = str(payload.get("prompt", ""))
                trace = TRACE_STORE.start("image", "image.render", model=agent.config().get("image", {}).get("model"), input_chars=len(prompt))
                try:
                    trace.event("image.synthesizing", steps=payload.get("steps"), size=payload.get("size"))
                    result = agent.generate_image(prompt, seed=payload.get("seed"), steps=payload.get("steps"), size=payload.get("size"))
                    trace.finish("ok", output_bytes=(agent.IMAGE_DIR / result["filename"]).stat().st_size, seed=result["seed"], steps=result["steps"], size=result["size"])
                    result["trace_id"] = trace.id
                    return json_response(self, result)
                except Exception as error:
                    trace.finish("error", error=str(error))
                    raise
            if self.path == "/api/run":
                return json_response(self, evaluation_service().run(payload.get("question", ""), payload.get("corpus"), payload.get("case_id")))
            if self.path == "/api/jobs":
                mode = payload.get("mode", "text")
                coordinator = HTML_COORDINATOR if mode == "html" else COORDINATOR
                job = coordinator.start(payload.get("question", ""), payload.get("corpus"), payload.get("case_id"), kind=mode)
                return json_response(self, {"job": job}, 202)
            if self.path == "/api/review":
                run = evaluation_service().review(payload.get("run_id", ""), payload.get("verdict"), payload.get("issues", []), payload.get("note", ""))
                return json_response(self, {"run": run}) if run else json_response(self, {"error": "Run not found."}, 404)
            if self.path == "/api/ask":
                question = str(payload.get("question", "")).strip()
                if not question:
                    return json_response(self, {"error": "Enter a question."}, 400)
                hits = agent.search(question, SETTINGS.retrieval_limit, payload.get("corpus"))
                answer, error = agent.synthesize(question, hits)
                return json_response(self, {"answer": answer, "error": error, "hits": hits, "mode": "model" if answer else "retrieval-fallback"})
            return json_response(self, {"error": "Not found"}, 404)
        except (ValueError, json.JSONDecodeError) as error:
            return json_response(self, {"error": str(error)}, 400)
        except Exception as error:
            return json_response(self, {"error": str(error)}, 500)


def main() -> None:
    print(f"Bonsai Agent UI: http://{SETTINGS.host}:{SETTINGS.port}")
    ThreadingHTTPServer((SETTINGS.host, SETTINGS.port), App).serve_forever()


if __name__ == "__main__":
    main()
