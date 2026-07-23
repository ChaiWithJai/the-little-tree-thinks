from __future__ import annotations

import json
import tempfile
import threading
import time
import unittest
from pathlib import Path

from bonsai_agent import ensure_preview_styles, finalize_generated_html

from bonsai_harness.catalog import CaseCatalog
from bonsai_harness.coordinator import RunCoordinator
from bonsai_harness.diagnostics import runtime_diagnostics
from bonsai_harness.domain import validate_corpus
from bonsai_harness.design_guidance import PAGE_CONTRACTS, evaluate_html_quality, guided_prompt, recovery_document
from bonsai_harness.html_service import HtmlGenerationService
from bonsai_harness.repository import SQLiteRunRepository
from bonsai_harness.service import EvaluationService
from bonsai_harness.state_machine import InvalidTransition, RunStateMachine
from bonsai_harness.tracing import LocalTraceStore


class FakeRag:
    model_id = "test-model"

    def __init__(self, answer: str | None = "Supported answer [S1]."):
        self.answer = answer

    def search(self, question: str, limit: int, corpus: str | None) -> list[dict]:
        return [{"path": "/local/source.md", "corpus": corpus or "civic", "chunk": 0, "score": 1.0, "text": "Supported evidence."}]

    def synthesize(self, question: str, hits: list[dict]) -> tuple[str | None, str | None]:
        return self.answer, None if self.answer else "empty"


class CatalogTests(unittest.TestCase):
    def test_corpus_names_are_portable_slugs(self):
        self.assertEqual(validate_corpus("creative_project"), "creative_project")
        with self.assertRaisesRegex(ValueError, "Corpus names"):
            validate_corpus("Private Notes")

    def test_catalog_is_validated_and_serialized(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text(json.dumps({
                "schema_version": 1,
                "cases": [{"id": "one", "title": "One", "question": "Question?", "corpus": None, "intent": "Inspect it."}],
                "review_issues": [{"id": "evidence", "label": "Evidence"}],
            }))
            payload = CaseCatalog(path).load()
            self.assertEqual(payload["cases"][0]["id"], "one")
            self.assertEqual(payload["review_issues"][0]["label"], "Evidence")

    def test_duplicate_case_ids_fail_fast(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            case = {"id": "same", "title": "One", "question": "Question?", "corpus": "civic", "intent": "Inspect it."}
            path.write_text(json.dumps({"schema_version": 1, "cases": [case, case], "review_issues": []}))
            with self.assertRaisesRegex(ValueError, "Duplicate case"):
                CaseCatalog(path).load()

    def test_frontend_benchmark_metadata_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            path.write_text(json.dumps({
                "schema_version": 1,
                "cases": [{
                    "id": "frontend-one", "title": "Frontend", "question": "Build it.",
                    "corpus": None, "intent": "Evaluate it.", "benchmark": "FrontendBench-inspired",
                    "category": "interaction", "acceptance": ["Keyboard works", "Tests pass"],
                }],
                "review_issues": [],
            }))
            case = CaseCatalog(path).load()["cases"][0]
            self.assertEqual(case["benchmark"], "FrontendBench-inspired")
            self.assertEqual(case["acceptance"], ["Keyboard works", "Tests pass"])

    def test_page_presets_cover_requested_page_family(self):
        path = Path(__file__).resolve().parents[1] / "evals" / "page-presets.json"
        payload = json.loads(path.read_text())
        presets = payload["presets"]
        self.assertEqual(len(presets), 6)
        self.assertEqual(
            {item["category"] for item in presets},
            {"moodboard", "product-page", "lookbook", "collection-guide", "editorial-guide", "collection-page"},
        )
        self.assertTrue(all(len(item["acceptance"]) == 4 for item in presets))
        self.assertTrue(all(item["source"] == "Rachel menswear study" and item["prompt"] for item in presets))


class RepositoryTests(unittest.TestCase):
    def test_legacy_import_is_idempotent_and_preserves_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "runs.json"
            legacy.write_text(json.dumps([{"id": "old", "created_at": 1, "case_id": "one", "corpus": None, "review": {"verdict": "pass"}}]))
            repository = SQLiteRunRepository(root / "runs.sqlite3", legacy)
            self.assertEqual(repository.recent(10)[0]["review"]["verdict"], "pass")
            SQLiteRunRepository(root / "runs.sqlite3", legacy)
            self.assertEqual(len(repository.recent(10)), 1)

    def test_review_update_is_transactional(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRunRepository(Path(directory) / "runs.sqlite3")
            repository.save({"id": "new", "created_at": 2, "case_id": None, "corpus": "civic", "review": None})
            updated = repository.update_review("new", {"verdict": "fail", "issues": [], "note": "No citation"})
            self.assertEqual(updated["review"]["verdict"], "fail")
            self.assertEqual(repository.get("new")["review"]["note"], "No citation")

    def test_interrupted_job_is_recovered_as_retryable_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRunRepository(Path(directory) / "runs.sqlite3")
            repository.save_job({
                "id": "job-one", "created_at": 1, "updated_at": 2, "state": "synthesizing",
                "question": "Question?", "corpus": None, "case_id": None, "run": None,
                "failed_stage": None, "error": None,
                "events": [{"state": "queued", "at": 1}, {"state": "retrieving", "at": 1.5}, {"state": "synthesizing", "at": 2}],
            })
            recovered = repository.recover_interrupted_jobs()
            self.assertEqual(recovered[0]["state"], "failed")
            self.assertEqual(recovered[0]["failed_stage"], "synthesizing")
            self.assertEqual(recovered[0]["error"]["kind"], "ProcessRestart")
            self.assertTrue(recovered[0]["error"]["retryable"])

    def test_coordinator_can_read_a_persisted_terminal_job(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteRunRepository(Path(directory) / "runs.sqlite3")
            job = {
                "id": "job-done", "created_at": 1, "updated_at": 2, "state": "awaiting_review",
                "question": "Question?", "corpus": None, "case_id": None, "run": {"id": "run-one"},
                "failed_stage": None, "error": None,
                "events": [{"state": "queued", "at": 1}, {"state": "awaiting_review", "at": 2}],
            }
            repository.save_job(job)
            coordinator = RunCoordinator(lambda: None, repository=repository)
            self.assertEqual(coordinator.get("job-done")["run"]["id"], "run-one")


class ServiceTests(unittest.TestCase):
    def make_service(self, root: Path, answer: str | None = "Supported answer [S1].") -> EvaluationService:
        return EvaluationService(
            FakeRag(answer),
            SQLiteRunRepository(root / "runs.sqlite3"),
            retrieval_limit=6,
            history_limit=30,
            allowed_issues={"unsupported-claim"},
        )

    def test_run_records_resolvable_citations(self):
        with tempfile.TemporaryDirectory() as directory:
            service = self.make_service(Path(directory))
            run = service.run("What is supported?", "civic", "case-one")
            self.assertTrue(run["checks"]["citations_resolve"])
            self.assertEqual(service.recent()[0]["id"], run["id"])

    def test_run_detects_unresolvable_citations(self):
        with tempfile.TemporaryDirectory() as directory:
            service = self.make_service(Path(directory), "Unsupported [S2].")
            run = service.run("What is supported?", None)
            self.assertFalse(run["checks"]["citations_resolve"])

    def test_review_rejects_taxonomy_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            service = self.make_service(Path(directory))
            run = service.run("What is supported?", "civic")
            with self.assertRaisesRegex(ValueError, "Unknown review issue"):
                service.review(run["id"], "fail", ["invented"], "")

    def test_observer_receives_canonical_pipeline_states(self):
        with tempfile.TemporaryDirectory() as directory:
            service = self.make_service(Path(directory))
            states = []
            service.run("What is supported?", "civic", observer=lambda stage, details: states.append(stage))
            self.assertEqual(states, ["retrieving", "synthesizing", "validating", "checkpointing"])


class HtmlGenerationTests(unittest.TestCase):
    def test_moodboard_guidance_is_specific_and_quality_is_measurable(self):
        prompt, contract = guided_prompt("Build a menswear board", "natural-uniform-moodboard")
        self.assertIn("asymmetric editorial board", prompt)
        self.assertIn(".material-grid", prompt)
        html = recovery_document("Build a menswear board", "natural-uniform-moodboard", "model stalled")
        quality = evaluate_html_quality(html, contract)
        self.assertGreaterEqual(quality["score"], 70)
        self.assertTrue(quality["checks"]["required_hooks"])

    def test_every_page_family_has_a_complete_recovery_contract(self):
        for case_id, contract in PAGE_CONTRACTS.items():
            with self.subTest(case_id=case_id):
                prompt, resolved = guided_prompt("Build the requested page", case_id)
                html = recovery_document("Build the requested page", case_id, "benchmark recovery")
                quality = evaluate_html_quality(html, resolved)
                self.assertIn("PAGE-TYPE CONTRACT", prompt)
                self.assertEqual(resolved["type"], contract["type"])
                self.assertIn("distillation", resolved)
                self.assertEqual(quality["score"], 100)
                self.assertTrue(all(quality["hooks"].values()))

    def test_known_page_recovers_from_a_stalled_local_model(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def stalled(_prompt):
                raise RuntimeError("first token timeout")

            service = HtmlGenerationService(
                stalled, SQLiteRunRepository(root / "runs.sqlite3"), root / "pages", "test-html-model",
            )
            run = service.run("Build the natural uniform", None, "natural-uniform-moodboard")
            self.assertTrue(run["generation"]["recovered"])
            self.assertGreaterEqual(run["quality"]["score"], 70)
            self.assertTrue((root / "pages" / run["artifact"]["filename"]).exists())

    def test_token_clipped_page_cannot_masquerade_as_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            clipped = '<!doctype html><html><head></head><body><main class="moodboard"><h1>Board</h1></main></body></html>'
            service = HtmlGenerationService(
                lambda _prompt: {"html": clipped, "telemetry": {"finish_reason": "length"}},
                SQLiteRunRepository(root / "runs.sqlite3"), root / "pages", "test-html-model",
            )
            run = service.run("Build the natural uniform", None, "natural-uniform-moodboard")
            self.assertTrue(run["generation"]["recovered"])
            self.assertEqual(run["quality"]["score"], 100)
            self.assertNotIn("bonsai-preview-base", run["answer"])

    def test_preview_styles_are_injected_once(self):
        html = "<!doctype html><html><head><title>Test</title></head><body><h1>Hello</h1></body></html>"
        styled = ensure_preview_styles(html)
        self.assertIn('id="bonsai-preview-base"', styled)
        self.assertEqual(ensure_preview_styles(styled).count('id="bonsai-preview-base"'), 1)

    def test_deadline_clipped_html_is_finalized_for_preview(self):
        prefix = '<!doctype html><html><head></head><body>'
        html = finalize_generated_html(prefix, '<main><h1>Moodboard</h1><style>main{color:olive}', bounded=True)
        self.assertIn('</style>', html)
        self.assertTrue(html.endswith('</html>'))
        self.assertIn('generation finalized at the local deadline', html)
        self.assertIn('id="bonsai-preview-base"', html)

    def test_html_service_checkpoints_a_previewable_document(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = SQLiteRunRepository(root / "runs.sqlite3")
            service = HtmlGenerationService(
                lambda prompt: "<!doctype html><html><head><style>body{color:black}</style></head><body><h1>Hello</h1></body></html>",
                repository, root / "pages", "test-html-model",
            )
            states = []
            run = service.run("Build a page", None, "html-case", observer=lambda stage, details: states.append(stage))
            self.assertEqual(states, ["retrieving", "synthesizing", "validating", "checkpointing"])
            self.assertEqual(run["mode"], "html")
            self.assertTrue(all(run["checks"].values()))
            self.assertTrue((root / "pages" / run["artifact"]["filename"]).exists())
            self.assertEqual(repository.get(run["id"])["artifact"]["url"], run["artifact"]["url"])

    def test_html_service_rejects_remote_scripts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service = HtmlGenerationService(
                lambda prompt: '<!doctype html><html><body><script src="https://example.com/app.js"></script></body></html>',
                SQLiteRunRepository(root / "runs.sqlite3"), root / "pages", "test-html-model",
            )
            with self.assertRaisesRegex(RuntimeError, "no_remote_scripts"):
                service.run("Build a page", None)

    def test_html_failure_reaches_terminal_coordinator_state(self):
        class FailingHtmlService:
            def run(self, question, corpus, case_id, *, observer):
                observer("retrieving", None)
                observer("synthesizing", None)
                raise RuntimeError("generation timed out")

        coordinator = RunCoordinator(lambda: FailingHtmlService())
        job = coordinator.start("Build a page", None, kind="html")
        deadline = time.monotonic() + 1
        while job["state"] not in {"failed", "awaiting_review"} and time.monotonic() < deadline:
            time.sleep(0.005)
            job = coordinator.get(job["id"])
        self.assertEqual(job["state"], "failed")
        self.assertEqual(job["failed_stage"], "synthesizing")
        self.assertTrue(job["error"]["retryable"])


class StateMachineTests(unittest.TestCase):
    def test_coordinator_persists_a_benchmark_trace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = SQLiteRunRepository(root / "runs.sqlite3")
            trace_store = LocalTraceStore(root / "runs.sqlite3")
            service = EvaluationService(
                FakeRag(), repository, retrieval_limit=6, history_limit=30,
                allowed_issues={"unsupported-claim"},
            )
            coordinator = RunCoordinator(lambda: service, repository=repository, trace_store=trace_store)
            job = coordinator.start("What is supported?", "civic", "trace-case")
            deadline = time.monotonic() + 1
            while job["state"] not in {"awaiting_review", "failed"} and time.monotonic() < deadline:
                time.sleep(.005)
                job = coordinator.get(job["id"])
            traces = trace_store.recent(10, "text")
            self.assertEqual(traces[0]["status"], "ok")
            self.assertEqual(traces[0]["attributes"]["case_id"], "trace-case")
            self.assertEqual([event["name"] for event in traces[0]["events"]][1:-1], [
                "queued", "retrieving", "synthesizing", "validating", "checkpointing", "awaiting_review",
            ])
            summary = trace_store.summary()
            self.assertIn("synthesizing", summary["by_kind"]["text"]["stages"])

    def test_happy_path_is_explicit(self):
        machine = RunStateMachine()
        for state in ["retrieving", "synthesizing", "validating", "checkpointing", "awaiting_review"]:
            machine.transition(state)
        self.assertEqual(machine.state, "awaiting_review")

    def test_illegal_transition_fails_fast(self):
        with self.assertRaisesRegex(InvalidTransition, "queued -> validating"):
            RunStateMachine().transition("validating")

    def test_coordinator_exposes_pollable_state_and_result(self):
        with tempfile.TemporaryDirectory() as directory:
            service = EvaluationService(
                FakeRag(),
                SQLiteRunRepository(Path(directory) / "runs.sqlite3"),
                retrieval_limit=6,
                history_limit=30,
                allowed_issues={"unsupported-claim"},
            )
            coordinator = RunCoordinator(lambda: service)
            job = coordinator.start("What is supported?", "civic", "one")
            deadline = time.monotonic() + 1
            while job["state"] not in {"awaiting_review", "failed"} and time.monotonic() < deadline:
                time.sleep(0.005)
                job = coordinator.get(job["id"])
            self.assertEqual(job["state"], "awaiting_review")
            self.assertEqual([event["state"] for event in job["events"]], ["queued", "retrieving", "synthesizing", "validating", "checkpointing", "awaiting_review"])
            self.assertEqual(job["run"]["case_id"], "one")

    def test_coordinator_applies_backpressure(self):
        entered = threading.Event()
        release = threading.Event()

        class BlockingService:
            def run(self, question, corpus, case_id, *, observer):
                observer("retrieving", None)
                entered.set()
                release.wait(1)
                observer("validating", {"retrieved_sources": 0})
                observer("checkpointing", {"citations_resolve": False})
                return {"id": question, "case_id": case_id}

        coordinator = RunCoordinator(lambda: BlockingService(), max_concurrent=1)
        first = coordinator.start("first", None)
        self.assertTrue(entered.wait(0.5))
        second = coordinator.start("second", None)
        self.assertEqual(coordinator.get(second["id"])["state"], "queued")
        release.set()
        deadline = time.monotonic() + 1
        while coordinator.get(second["id"])["state"] != "awaiting_review" and time.monotonic() < deadline:
            time.sleep(0.005)
        self.assertEqual(coordinator.get(first["id"])["state"], "awaiting_review")
        self.assertEqual(coordinator.get(second["id"])["state"], "awaiting_review")


class FirstUseUxContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        cls.html = (root / "web" / "index.html").read_text()
        cls.script = (root / "web" / "app.js").read_text()
        cls.styles = (root / "web" / "styles.css").read_text()

    def test_day_zero_starts_with_one_agent_and_optional_journeys(self):
        self.assertIn('id="agent-start"', self.html)
        self.assertIn("What should Bonsai", self.html)
        self.assertEqual(self.html.count("data-journey "), 6)
        for label in ("Launch a product", "Research a decision", "Build a storyboard", "Recover a failed run"):
            self.assertIn(label, self.html)
        self.assertIn("inferMode", self.script)
        self.assertIn("Models, sources, and generated work stay on this machine", self.html)

    def test_first_use_defers_harness_chrome(self):
        self.assertIn(".day-zero .statebar", self.styles)
        self.assertIn(".prompting .statebar", self.styles)
        self.assertIn("Show run details", self.html)
        self.assertIn("technical-event", self.script)
        self.assertIn("reviewing.show-details .technical-event", self.styles)

    def test_prompt_review_and_export_have_accessible_contracts(self):
        self.assertIn('aria-describedby="composer-hint composer-error"', self.html)
        self.assertIn('role="alert"', self.html)
        self.assertIn('aria-live="polite"', self.html)
        self.assertIn("Export HTML", self.script)
        self.assertIn("Your page is ready", self.script)

    def test_routes_drafts_and_history_are_explicit_state(self):
        self.assertIn("bonsai-drafts-v1", self.script)
        self.assertIn("routeFromLocation", self.script)
        self.assertIn("/api/runs/${route.id}", self.script)
        self.assertIn("window.addEventListener('popstate',applyRoute)", self.script)
        self.assertIn("writeRoute(`/jobs/${data.job.id}`)", self.script)
        self.assertIn("writeRoute(`/runs/${job.run.id}`", self.script)

    def test_server_shell_and_cache_policy_support_deep_links(self):
        server = (Path(__file__).resolve().parents[1] / "bonsai_agent_web.py").read_text()
        for route in ('"/draft"', '"/jobs"', '"/runs"'):
            self.assertIn(route, server)
        self.assertIn('"/api/runs/"', server)
        self.assertIn('"no-store"', server)
        self.assertIn('max-age=31536000, immutable', server)
        self.assertIn('stale-while-revalidate=300', server)

    def test_result_markdown_and_responsive_reading_surface_are_structured(self):
        for feature in ("markdownBody", "inlineMarkdown", "table-scroll", "code-block", "copy-result", "source-peek"):
            self.assertIn(feature, self.script)
        self.assertIn('aria-label="Scrollable result table"', self.script)
        self.assertIn(".markdown-body", self.styles)
        self.assertIn("max-width:74ch", self.styles)
        self.assertIn("height:100dvh", self.styles)
        self.assertIn("@media(max-width:420px)", self.styles)


class DiagnosticTests(unittest.TestCase):
    def test_optional_runtime_failures_do_not_block_ready_harness(self):
        items = runtime_diagnostics(
            text={"reachable": True, "models": ["bonsai-mlx"]},
            embedding={"ready": False, "error": "missing worker"},
            image={"ready": True, "pipeline_uses_bundled_vae": True, "demo_dir": "/local/demo"},
            index_ready=True,
            chat_model="bonsai-mlx",
        )
        self.assertFalse(any(item["blocking"] for item in items))
        self.assertEqual(next(item for item in items if item["id"] == "embedding")["severity"], "bypassed")

    def test_missing_configured_text_model_is_a_real_blocker(self):
        items = runtime_diagnostics(
            text={"reachable": True, "models": ["some-other-model"]},
            embedding={"ready": False}, image={"ready": False}, index_ready=True, chat_model="bonsai-mlx",
        )
        synthesis = next(item for item in items if item["id"] == "synthesis")
        self.assertTrue(synthesis["required"])
        self.assertTrue(synthesis["blocking"])


if __name__ == "__main__":
    unittest.main()
