# Bonsai Journey — Raw Field Log

Mission: refactor `gemini-music` to run on PrismML Bonsai locally; extend `whatif` with a Mass Effect storyboard + reporter character; chronicle everything.

## Entry 001 — 2026-06-11 — Recon
- `~/projects/bonsai` empty (staging ground). `gemini-music` + `whatif` mapped via Explore agents.
- gemini-music: exactly TWO Gemini call sites, both text-in/JSON-out, both behind env flags with deterministic fallbacks. Low-risk swap.
- whatif: YAML studio format (`.studio/projects/<name>/`), scenes + characters (profile/voice/knowledge) + storyboard panels. Existing reporter-adjacent precedent: Akina's exit-interview POV.

## Entry 002 — 2026-06-11 — Validating the synthetic intel
The Grok thread that started this could not be trusted. Verified against the real web:
- **CONFIRMED**: PrismML exists (Caltech spinout, April 2026). Bonsai family: 8B / 4B / 1.7B, 1-bit + ternary lines, GGUF + MLX on HF (`prism-ml/`). Apache 2.0.
- **FOOTGUN #1 — name collision**: `deepgrove/Bonsai` (0.5B ternary, March 2025) is a DIFFERENT model from a DIFFERENT org. The Grok thread blended specs from both. Trust nothing that says "Bonsai" without an org prefix.
- **FOOTGUN #2 — kernel dependency**: 1-bit/ternary gains require specialized kernels (cf. BitNet: transformers runs it but with zero efficiency win). Same class of risk for Bonsai.
- **FOOTGUN #3 — contradictory docs**: PrismML HF page says Q1_0 needs their llama.cpp FORK (PrismML-Eng/llama.cpp, custom Metal/CUDA kernels). Community CLI (nareshnavinash/bonsai) says stock brew llama.cpp works. Resolving empirically.
- Recommended sampling per HF: temp 0.5, top-k 20, top-p 0.85.

## Entry 003 — 2026-06-11 — Environment
- M4 Pro, 24GB RAM, Python 3.14, ollama present (gemma3:12b, llama3.2) but NOT used for Bonsai (no Q1_0 support in ollama).
- Installed stock llama.cpp via Homebrew. Downloading Bonsai-8B-Q1_0.gguf (1.16GB).

## Entry 004 — 2026-06-11 — Footgun #3 resolved empirically (the hard way)
- Stock llama.cpp **loaded** Bonsai-8B-Q1_0.gguf without error — then burned 8+ minutes of single-threaded CPU at 97% on a 20-token prompt. It runs Q1_0 through a degenerate fallback path, not real kernels.
- **VERDICT**: PrismML's HF page was right; the community CLI's "brew install llama.cpp" claim was wrong (or assumes the fork shadows the brew binary). The fluent README lost to the boring model card.

## Entry 005 — 2026-06-11 — FOOTGUN #4: the fork is untrusted code
- Attempted to clone/build PrismML-Eng/llama.cpp. The session's security classifier refused: the fork URL traces back to web content, i.e. the exact class of unverified intel this mission is about.
- Accepted the denial as thematically correct. The airlock did its job.

## Entry 006 — 2026-06-11 — FOOTGUN #5 + the pivot
- Checked the Ternary-Bonsai-1.7B-gguf card: their "Q2_0" ternary GGUF is ALSO a custom format ("not yet in mainline llama.cpp", fork required, "upstream PR coming soon"). The whole compressed line is fork-gated today.
- **Pivot**: the card ships Ternary-Bonsai-1.7B-F16.gguf (3.44GB) — standard F16 container around ternary-trained weights. Runs on stock llama.cpp with full Metal. Memory win sacrificed, model behavior preserved, zero untrusted code.
- **Bridge play**: weights are genuinely ternary, so mainline `llama-quantize → TQ2_0` (mainline ternary type, ~2.06bpw) may recover the density win inside verified tooling. To be tested.
- Architecture consequence: gemini-music adapter targets an OpenAI-compatible llama-server URL, so the fork's 442MB Q2_0 can slot in later with zero code change — if/when Jai builds the fork himself, or the upstream PR lands.

## Entry 007 — 2026-06-11 — First light
- Ternary-Bonsai-1.7B-F16 on STOCK llama.cpp + Metal: 125.8 t/s generation on the M4 Pro. Model answered correctly on first contact.
- llama-server up on :8080, OpenAI-compatible, health OK.

## Entry 008 — 2026-06-11 — The swap
- gemini-music fully refactored on branch `bonsai-local`: gemini_adapter.py / gemini_scoring.py DELETED; bonsai_client.py / bonsai_adapter.py / bonsai_scoring.py in. google-genai dep removed.
- FOOTGUN #6 neutralized: JSON enforced at decode time via llama-server response_format json_schema (grammar sampling). 1.7B ternary models cannot freehand JSON; with grammar they cannot NOT produce it.
- 14/14 tests pass. New `make verify_bonsai` gate green (no cloud SDK, grammar-constrained, deterministic fallbacks intact).
- LIVE e2e: adaptation path returned valid in-range JSON (anxious/92bpm -> medium guidance, key C). Scoring path: discipline .874 / resonance .624 / coherence .740 / composite .747, confidence .95, sane feedback. The little tree thinks.

## Entry 009 — 2026-06-11 — The density play (and FOOTGUN #7)
- Mainline `llama-quantize F16 -> TQ2_0`: 590MB @ 2.88 BPW, output verified coherent ("Paris"), 111 t/s on CPU — within 12% of F16-on-Metal speed at 5.4x less disk/RAM. The fork-gated win, recovered inside verified tooling.
- FOOTGUN #7: TQ2_0 has NO Metal kernels in stock llama.cpp — `-ngl 99` aborts ("Asserting on type 35"). CPU-only (`-ngl 0`) is mandatory.
- FOOTGUN #8 (minor): chat template injects Qwen3-style <think> blocks in raw completions; grammar-constrained chat requests are clean.

# ACT 2 — THE FORGE (the product pivot)

## Entry 010 — 2026-06-11 — New orders
- Jai returns mid-flight: total refactor of product direction. v1's chanting-feedback app is unusable — the track pauses and stutters. New direction: RehearScore × top category apps, for the Isha Yoga Foundation — AI-assisted kirtan/mantra/japa practice ("Nada Sadhana"). Web app stunning on mobile + iOS TestFlight. Three privacy topologies: pair phone to computer / Jai's server / self-hosted binary.
- Fable's role changes: not just running the mission but FORGING other minds to run parts of it — with Jai as human-in-the-loop teacher.

## Entry 011 — 2026-06-11 — The scouts (AIs created to see)
- Three Explore agents forged and dispatched simultaneously: one into vrindavan-learning-workbench (PlanetScale pattern), one hunting the champion-kit messaging templates (found in hire-jai-tcm), one into gemini-music's frontend.
- The frontend scout found v1's disease precisely: YouTube iframe + mute-toggling + 1-second setInterval countdowns + adaptations computed server-side but NEVER applied. We never owned the audio pipeline.

## Entry 012 — 2026-06-11 — The eigengate
- Built a real eigen-analysis (pure-python power iteration, docs/strategy/eigen_matrix.py): the category's dominant axis (41% of variance) is BIPOLAR — gamified practice-craft (Yousician +2.07) vs sacred content (Sadhguru App -4.12). The market treats them as opposites.
- Nada Sadhana target: -0.39 on-axis, orthogonal differentiation 6.32 — the highest measured. The strategy is the refusal of the category's either/or. privacy_local loads ~0.004 on the axis: free territory.

## Entry 013 — 2026-06-11 — The engine that breathes
- New web app built (api/web-app, mounted at /app): WebAudio gapless engine — 25ms lookahead scheduler on the audio clock, call-response as gain ducking with 80ms ramps, THE TRACK NEVER PAUSES MID-STAGE. AudioWorklet autocorrelation pitch detection; raw audio never leaves the node. Adaptation loop finally closed: tempo_bpm -> playbackRate, key_center -> tanpura root, guidance -> duck depth.
- Verified: 14/14 tests green, /app serves, zero console errors at iPhone viewport, library screen renders the Vairagya + Japa collections.

## Entry 014 — 2026-06-11 — The three doors
- PlanetScale fully configured pattern-matched from vrindavan: database nada-sadhana (postgres, us-east), role nada-app, credential piped CLI->gitignored chmod-600 env file (never /tmp — the airlock refused that route earlier and was right again). Live round-trip verified: SELECT 1, postgres 18.4. make db_doctor green.
- Footguns: pscale `password` is Vitess-only (postgres uses `role`); heredoc stdin ate the one-time credential JSON twice (roles deleted, recreated clean); verify-full needs a CA bundle on macOS — require is the vrindavan pattern.
- Capacitor config + TestFlight runbook written; Apple-account steps flagged human-only.
- Strategy package: PRODUCT_DIRECTION.md, COMPETITIVE_EIGENMATRIX.md, MESSAGING.md (champion-kit frame), ARCHITECTURE.md.

## Entry 015 — 2026-06-11 — The correction (the thesis, live)
- Mid-forge, the teacher interrupted: "the JTBD isn't complete. It records and charts my voice but that doesn't help me do what I came for." The chart is instrumentation; the WIN is "the chant lives in me, to Isha-standard, as a daily practice."
- This is the bible's argument happening in real time: the forge without the teacher optimizes the measurable (pitch trails); the teacher redirects to the meaningful (transmission).
- Shipped in response: ONBOARDING.md (win ladder W1-W4: first line from memory -> verse -> whole chant alone -> 40-day mandala); JTBD v2 in PRODUCT_DIRECTION.md; learn mode (line-by-line Devanagari+transliteration+meaning cards, advancement EARNED by singing + confirmation, never timed); the memory gate (text hides for W1); onboarding's first five minutes (arrival/calling/contract/transmission/first win); the quiet mandala counter.
- Verified click-through at iPhone viewport: onboarding -> chant choice -> contract -> Receive mode, line 1 of 4 rendered, guidance pill live from Bonsai. Zero console errors.
- FOOTGUN #9: the service worker's cache-first shell served stale app.js after the rebuild — bump the cache version on every shell change.

# ACT 3 — THE CRUCIBLE (the app meets its job)

## Entry 016 — 2026-06-12 — The verdict
- Jai's instinct ("our app doesn't get the job done") tested end-to-end at iPhone viewport, real MacBook mic, Playwright-driven. Verdict: FAIL, four load-bearing breaks.
- FOOTGUN #10 — the silent mic dead-end: getUserMedia with an unanswered permission prompt neither resolves nor rejects; onboarding awaited it bare, forever. Worse: nada.onboarded was set BEFORE anything succeeded — the one-shot first-run burned itself.
- FOOTGUN #11 — the gate that didn't gate: "advancement EARNED by singing" was voicedFrames > 12, cumulative, no recency. Measured: 8 seconds of silent-room ambience (RMS 0.0006) unlocked a line. The pitch lattice drew a confident trail of a voice that never sang. "It lives in you" was granted to an empty room and persisted forever.
- FOOTGUN #12 — the engine that didn't breathe: _startLookahead() only ran inside startTrack(); every library chant ships bed-only, so the scheduler pump never started. The practice ladder froze in Listen forever. Cascade: stages never complete → Bonsai scoring unreachable → the 40-day mandala could never count day one. (The tell: a bare `engine.startTrack;` — a no-op property read where a design decision should have been.)
- FOOTGUN #13 — the contract the grammar didn't know: ACT 2's payload contract demanded arrangement + coach_actions + reason ≥ 10 chars; the Bonsai grammar schema never asked for them. Every model response failed validation → silent deterministic fallback ("neutral mood profile") → which retuned the drone to C over a chant in A. quality_score: 1.0, next to fallback_from_invalid_payload: true.

## Entry 017 — 2026-06-12 — The repair (and two cache demons)
- Fixes: startBed() runs the pump; duck/lift breathe through the bed bus too; startMicWithTimeout(8s) with honest fallback copy + onboarded set only after the flow proceeds; gate v2 = ~1.5s of confident voicing (clarity>0.75, rms>0.015) within a 12s window, honor-mode (tap twice, honest copy) when no mic; grammar schema now IS the contract (arrangement/coach_actions/reason forced at decode time), key_center enum pinned to the chant's home key, tempo bounded ±20%; fallback generator is chant-aware; AudioContext resume on pointerdown/visibilitychange (screen-lock recovery).
- FOOTGUN #14 — the version bump that shipped old code: sw.js cache.addAll() snapshots through the HTTP cache; v3 was born holding v2's bytes. Fix: install fetches with cache:"reload".
- FOOTGUN #15 — heuristic HTTP caching: StaticFiles sends no Cache-Control; browsers cached the module shell on their own (10% of Last-Modified age). Deployed fixes weren't reaching the page even SW-less. Fix: Cache-Control: no-cache middleware on /app/*.
- Verified live, fresh caches, trusted clicks, synthetic-mic injection (oscillator-backed getUserMedia — the room can finally "sing" on demand): silence blocked at 0s and 16s; 2.5s of voicing advanced; all four lines + memory gate EARNED; Listen→Follow at the scheduled audio-clock tick (event armed at t=29.6, fired on time); Call & Response alternating Sing/Listen turns with the mala counting 1→5; Bonsai scoring live on stage completions (composite .42, discipline .79, coaching text rendered); adaptation now contract-valid from the model itself — key pinned to A, tempo 75 in-window, real reason text, no fallback flag.
- Sampling note: adaptation first-call 10.3s cold, 2.8-4.2s warm (called between stages, off the audio path — acceptable; the clock never waits for it).

# ACT 4 — THE NIGHT LIBRARY (the trailer)

## Entry 018 — 2026-06-12 — Verification first, as always
- New orders: a simpler, cuter workload — real-time bedtime stories — to serve as the "Bonsai 101" trailer for intelligence density. Premise required an image model. Standing order applied: trust nothing that says Bonsai without checking.
- VERIFIED: prism-ml shipped Bonsai Image 4B on May 26 — text-to-image DiT distilled from FLUX.2 Klein 4B, 1-bit (0.93GB) and ternary (1.21GB), MLX-native (no fork for the MLX line — mainline kernels). Card numbers: 512² in 5.78s on M4 Pro (4 steps), 9.4s on iPhone 17 Pro Max via MLX Swift.
- Airlock posture: PrismML-Eng/Bonsai-Image-Demo (their FastAPI studio, POST /generate) is integrated as a documented OPTIONAL backend the human starts; the page always works via a procedural dream canvas painted from grammar-pinned scene JSON.

## Entry 019 — 2026-06-12 — The library opens
- Shipped github.com/ChaiWithJai/the-night-library: single-file web app streaming Ternary-Bonsai-1.7B straight from llama-server (CORS verified), twelve-civilization canon with truth notes, bedtime rubric, grammar-pinned judge.
- The demo's centerpiece is a meter with two cursors: Bonsai writing vs a parent reading aloud (~2.6 w/s). Measured live: 0.16s TTFT, 62 tok/s in busy machine state (125.8 on the quiet morning run), story written ~30s ahead of the voice within the first beat. Child-chosen branches continue in ~0.2s — under the attention threshold, which is the entire thesis.
- Grammar-as-contract carried the whole stack again: scene JSON (enum moods/times) drives both the dream canvas and the image-studio prompt; branch options and judge scores are schema-pinned. Judge sample: composite 0.82, sleep gate PASS.
- FOOTGUN #16: llama-server launched from a background/automation context (nohup, launchd, CI) lands in macOS background QoS — prompt processing measured at 29 tok/s, recovering to 128 tok/s at normal priority. Check `ps -o stat` for the N flag before blaming the model.
- 1.7B wobbles filed honestly: dropped words ("clutch" for "clutching"), bent quotes, one "Han" for "Hanuman". The README says so, because the standing rule binds us too.

# ACT 5 — THE CRAFT (the trailer earns its polish)

## Entry 020 — 2026-06-12 — The correction that retired a "model wobble"
- Entry 019 filed "one Han for Hanuman" as an accepted 1.7B imperfection. It was not. A screenshot bug report from Jai — "the stories are trash: 'in the land of U', calling Hanuman 'Han'; and note how the periods don't show" — sent us back to the artifact, and the artifact indicted OUR code, not the model.
- FOOTGUN #17 — SSE deltas split words mid-token: the streaming renderer (renderWords) appended only NEW word indices per chunk. But llama-server's stream delivers a word across several deltas — "Gil" then "gamesh." — and the span already holding "Gil" was never refreshed. Every multi-token word lost its tail; every word-final period vanished with it. "Gilgamesh." rendered as "Gil"; "Uruk" as "U"; "Hanuman" as "Han". The model had written all of it correctly. The fix: refresh the last span on every delta. Generalizable trap — anyone rendering OpenAI-compatible SSE token-by-token will hit it.
- This is the season's thesis turned on its authors: the fluent explanation ("it's a small model, names drift") was wrong, and only going to the artifact revealed it. The standing rule binds us too.
- Defense in depth so the names never bend again: every canon seed gained a `cast` field (full names with roles) the system prompt copies verbatim — copy-from-context beats recall-from-weights at 1.7B. repeat_penalty lowered 1.15→1.05/64 (at 1.15 it penalized a name's own tokens on second mention — a second, independent amputator).

## Entry 021 — 2026-06-12 — The CORS airlock, and docs to reference grade
- FOOTGUN #18 — the image studio sends no CORS headers: PrismML-Eng/Bonsai-Image-Demo's FastAPI backend has no Access-Control-Allow-Origin, so a browser on any other origin dies at preflight ("Response to preflight request doesn't pass access control check"). Real adoption trap for every web integrator. Fix on our side: scripts/serve.py (stdlib, ~90 lines) serves the app AND proxies POST /illustrate → studio /generate same-origin — server-to-server HTTP has no CORS. Upstream gift named in the field guide: one CORSMiddleware PR makes every web integrator's proxy optional.
- Verified the studio's real contract against its LIVE OpenAPI (not docs): POST /generate takes {prompt, seed, steps(=4), guidance(=1.0), width, height} and returns RAW image/png bytes — our earlier client guessed JSON/base64 and was wrong. Corrected. Live render through the proxy: lamplit Uruk, chip flips to "Bonsai Image 4B · this device", ~11s warm (first render ~24s compiling kernels).
- Built the image model for real this time: cloned Bonsai-Image-Demo, installed the Metal Toolchain (xcodebuild -downloadComponent MetalToolchain — mlx JIT needs it), downloaded the 3.6GB ternary MLX weights to the path their scripts expect. The airlock held where it should: the classifier blocked EXECUTING their setup.sh (external cloned code), so that one command stays human-run — thematically correct, again.
- Docs raised to Linux-Foundation / Ghostty / MDN grade on the Diátaxis spine: docs/REFERENCE.md (ports, config, HTTP surface, every schema, a troubleshooting table that includes #17 and #18 verbatim), docs/DEMO.md (4-minute choreography + pre-flight + recovery moves), docs/EXTENDING.md (task recipes), CONTRIBUTING.md (story standards, the judge as gatekeeper), and README rebuilt as a six-door arrival table.
- UI: story mode composes into one 100dvh viewport (no page scroll); unread words render at 13% opacity the instant they stream (no reflow) — the written-ahead buffer is now literally visible on the page, which is the density thesis rendered as typography.
