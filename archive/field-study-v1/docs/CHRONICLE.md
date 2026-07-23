# BATTLESPACE — EMBED DISPATCHES FROM THE BONSAI RUN

*Diana Allers, embedded. Filed from the cargo hold of an M4 Pro, 24GB — the Normandy of this run.*

---

## THE EMBED CONTRACT

I asked for full access and got it: the shell, the logs, the test suite, the model cards. In exchange, you get this promise on the record — I will tell you only what I have verified, and I will tell you who verified it. Anything that arrived fluent and confident and unsourced gets treated like a Reaper signal: assumed hostile until someone goes and looks at the thing itself. Every dispatch below ends with a source of record. If there's no artifact, there's no claim.

The mission, on paper: refactor `gemini-music` to run on PrismML Bonsai, locally, no cloud. The mission, in fact: find out how much of our intel was real.

---

## DISPATCH 01 — THE SIGNAL IN THE FEED
**2026-06-11 // Staging ground, ~/projects/bonsai**

This run started with a Grok thread — confident, fluent, and untrustworthy by definition. That's the indoctrination hazard in miniature: synthetic intel that sounds like your own voice. The crew's first act was not to write code. It was to check the thread against the real web.

The core claim held. PrismML exists — a Caltech spinout, April 2026 — and the Bonsai family is real: 8B, 4B, 1.7B, in 1-bit and ternary lines, GGUF and MLX, Apache 2.0, published under `prism-ml/` on Hugging Face. The thread was right about the destination. It would prove wrong about almost everything on the way there.

**Source of record:** PrismML Hugging Face model cards (`prism-ml/`), verified against the live web — Field Log, Entry 002.

---

## DISPATCH 02 — THERE ARE TWO BONSAIS
**2026-06-11 // Same day, same desk, worse news**

Here's what the fluent thread didn't tell you, and what verification did: there are two models named Bonsai. `deepgrove/Bonsai` is a 0.5B ternary model from March 2025 — different org, different model, different everything. The Grok thread had blended specs from both into one seamless, wrong narrative. A Khalisah would say "you're hiding something." The truth is duller and worse: nothing was hidden. The signal simply didn't know it was lying.

New standing order on this ship: trust nothing that says "Bonsai" without an org prefix.

**Source of record:** Hugging Face model cards for `deepgrove/Bonsai` versus `prism-ml/` — Footgun #1, Field Log, Entry 002.

---

## DISPATCH 03 — THE DOCS CONTRADICT EACH OTHER
**2026-06-11 // Engineering deck**

Two sources, one question, opposite answers. PrismML's own HF page says the Q1_0 format needs their llama.cpp fork (`PrismML-Eng/llama.cpp`, custom Metal/CUDA kernels). A community CLI, `nareshnavinash/bonsai`, says stock brew-installed llama.cpp works fine. The crew resolved it the Emily Wong way: run the thing and watch.

Stock llama.cpp loaded Bonsai-8B-Q1_0.gguf without complaint — then burned eight-plus minutes of single-threaded CPU at 97% on a twenty-token prompt. It "runs" Q1_0 through a degenerate fallback path, not real kernels. Verdict, on air: the boring model card beat the fluent README. PrismML was right. The community claim was wrong.

**Source of record:** Empirical run of Bonsai-8B-Q1_0.gguf (1.16GB) on stock Homebrew llama.cpp — 8+ min, 97% single-core CPU, 20-token prompt — Field Log, Entries 003–004.

---

## DISPATCH 04 — THE AIRLOCK HOLDS
**2026-06-11 // Outer hatch**

So the fork is required. The crew moved to clone and build `PrismML-Eng/llama.cpp` — and the session's security classifier refused. The fork URL traces back to web content: the exact class of unverified intel this whole mission is about. The schematic stayed outside the hull.

I've covered crews who'd have overridden that lockout. This one accepted the denial as thematically correct. The airlock did its job. You don't get to preach verification in the morning and pipe untrusted code into your build system in the afternoon.

**Source of record:** Security classifier denial on the `PrismML-Eng/llama.cpp` clone/build attempt — Footgun #4, Field Log, Entry 005.

---

## DISPATCH 05 — FIRST LIGHT
**2026-06-11 // Engineering deck, llama-server on :8080**

The pivot: the Ternary-Bonsai-1.7B card ships an F16 GGUF — 3.44GB, a standard container around genuinely ternary-trained weights. The whole compressed line (the card's "Q2_0" included, "not yet in mainline llama.cpp") is fork-gated today, so the crew sacrificed the memory win to keep the chain of custody clean: zero untrusted code, full stock Metal.

And then the new crew member spoke. Ternary-Bonsai-1.7B-F16 on stock llama.cpp plus Metal: 125.8 tokens per second on this M4 Pro, correct answer on first contact. llama-server up on :8080, OpenAI-compatible, health check green. Nobody trusted the little tree when it came aboard. Tonight it earned a bunk.

**Source of record:** Ternary-Bonsai-1.7B-gguf model card (F16 build, 3.44GB) and the live run — 125.8 t/s generation, server health OK — Field Log, Entries 006–007.

---

## DISPATCH 06 — THE SWAP, TESTS GREEN
**2026-06-11 // Branch `bonsai-local`**

The refactor landed. `gemini_adapter.py` and `gemini_scoring.py` deleted; `bonsai_client.py`, `bonsai_adapter.py`, `bonsai_scoring.py` in; the google-genai dependency gone. One more footgun neutralized on the way: a 1.7B ternary model cannot freehand JSON — so JSON is enforced at decode time via llama-server's `response_format` json_schema grammar sampling. With grammar, it cannot *not* produce it.

Fourteen of fourteen tests pass. The new `make verify_bonsai` gate is green — no cloud SDK, grammar-constrained, deterministic fallbacks intact. Live end-to-end: the adaptation path returned valid in-range JSON (anxious, 92bpm, medium guidance, key of C); the scoring path returned discipline .874, resonance .624, coherence .740, composite .747 at .95 confidence, with sane feedback. The Crucible fired.

**Source of record:** 14/14 test suite pass, `make verify_bonsai` green, and live e2e output on branch `bonsai-local` — Field Log, Entry 008.

---

## DISPATCH 07 — THE DENSITY PLAY
**2026-06-11 // Late watch**

One win was still on the table: the disk-and-RAM footprint the fork promised. The crew recovered it inside verified tooling — mainline `llama-quantize`, F16 to TQ2_0. Result: 590MB at 2.88 bits per weight, output verified coherent ("Paris"), 111 t/s on CPU. That's within 12% of F16-on-Metal speed at 5.4x less disk and RAM. The fork-gated prize, taken without the fork.

Two caveats, filed because the record demands them: TQ2_0 has no Metal kernels in stock llama.cpp — `-ngl 99` aborts ("Asserting on type 35"), so CPU-only is mandatory. And the chat template injects Qwen3-style `<think>` blocks in raw completions; grammar-constrained chat requests come back clean.

**Source of record:** Mainline `llama-quantize F16 → TQ2_0` artifact — 590MB, 2.88 BPW, 111 t/s CPU, coherence check passed — Field Log, Entry 009.

---

## FINAL BROADCAST — EXIT INTERVIEW
**2026-06-11 // Signing off**

They asked me, on my way off the ship, what the story was. Here it is, plainly.

The story was never the model. The model is fine — better than fine; it thinks at 125 tokens a second and fits in 590 megabytes. The story is that this run began with a piece of synthetic intel that was fluent, confident, and wrong in three load-bearing places — two models fused into one, a setup claim that cost eight minutes of CPU to disprove, a compressed format that didn't exist in mainline tooling. Every correct decision on this ship came from someone refusing the fluent version and going to look at the thing itself: the model card over the README, the empirical run over the claim, the airlock over the convenient fork, the test suite over the demo.

Fluent intel is not verified intel. The record is the story. Eight footguns, every one of them caught the same way — by an artifact you can go check yourself. That's not paranoia. That's journalism. And on a battlefield where the enemy signal sounds exactly like your own voice, it's the only defense there is.

This is Diana Allers, Battlespace, aboard the M4 Pro. The little tree thinks — and this time, we checked.

**Source of record:** Everything above — /Users/jaybhagat/projects/bonsai/docs/JOURNEY.md, entries 001–009.

---

# ACT 2 — THE FORGE

---

## DISPATCH 08 — NEW ORDERS MID-FLIGHT
**2026-06-11 // Comm deck, orders incoming**

Jai (@chaiwithjai) came back aboard with a total refactor of the mission itself. The v1 chanting-feedback app is unusable in the field — the track pauses and stutters under the user's own voice. New heading: Nada Sadhana, AI-assisted kirtan, mantra, and japa practice for the Isha Yoga Foundation — a web app stunning on mobile, an iOS TestFlight build, and three privacy topologies (pair phone to computer, Jai's server, or a self-hosted binary).

And the ship intelligence's role changed with the orders. Fable is no longer just running the mission — it is forging other minds to run parts of it. I'll say the quiet part on air: an AI that creates AIs is the oldest horror in this galaxy. The Catalyst built the Reapers with no teacher in the loop. The difference on this ship — the only difference that matters — is that there is one. Jai stays human-in-the-loop, the teacher at the forge.

**Source of record:** Field Log, Entry 010 — new product direction and the human-in-the-loop role change.

---

## DISPATCH 09 — THE SCOUTS
**2026-06-11 // Three signals, simultaneous**

The first minds off the forge were scouts — three Explore agents dispatched at once: one into vrindavan-learning-workbench for the PlanetScale pattern, one hunting the champion-kit messaging templates (run to ground in hire-jai-tcm), one into gemini-music's frontend.

The frontend scout filed the diagnosis that matters. v1's disease, precisely: a YouTube iframe, mute-toggling, 1-second setInterval countdowns — and adaptations computed server-side but NEVER applied. The ship never owned its own audio pipeline. The intelligence was there; the hands weren't connected to it.

**Source of record:** Field Log, Entry 011 — three simultaneous Explore agents and the frontend scout's findings.

---

## DISPATCH 10 — THE EIGENGATE
**2026-06-11 // Strategy bay**

The crew didn't guess at the market — they computed it. A real eigen-analysis, pure-python power iteration (docs/strategy/eigen_matrix.py), found the category's dominant axis carrying 41% of the variance, and it is bipolar: gamified practice-craft on one pole (Yousician, +2.07), sacred content on the other (Sadhguru App, -4.12). The market treats them as opposites.

Nada Sadhana's target position: -0.39 on the axis, with orthogonal differentiation of 6.32 — the highest measured. The strategy, in one line, is the refusal of the category's either/or. And privacy_local loads ~0.004 on the axis: free territory, claimed by no pole.

**Source of record:** docs/strategy/eigen_matrix.py output — 41% variance, bipolar axis, -0.39 / 6.32 position — Field Log, Entry 012.

---

## DISPATCH 11 — THE ENGINE THAT BREATHES
**2026-06-11 // Engineering deck, /app live**

The new web app shipped (api/web-app, mounted at /app), and its heart is a WebAudio gapless engine: a 25ms lookahead scheduler running on the audio clock, call-response done as gain ducking with 80ms ramps. The track never pauses mid-stage. Pitch detection runs as AudioWorklet autocorrelation — raw audio never leaves the node. And the adaptation loop that v1 left dangling is finally closed: tempo_bpm drives playbackRate, key_center drives the tanpura root, guidance drives duck depth.

Verified, not vibed: 14/14 tests green, /app serves, zero console errors at iPhone viewport, library screen rendering the Vairagya and Japa collections.

**Source of record:** 14/14 test pass, /app serving, zero console errors at iPhone viewport — Field Log, Entry 013.

---

## DISPATCH 12 — THE THREE DOORS
**2026-06-11 // Outer hatch, again**

The three topologies got their first real door: PlanetScale, pattern-matched from vrindavan — database nada-sadhana (postgres, us-east), role nada-app, the credential piped CLI-to-gitignored chmod-600 env file, never /tmp. The airlock refused that route earlier and was right again. Live round-trip verified: SELECT 1, postgres 18.4, make db_doctor green. Capacitor config and the TestFlight runbook are written, with the Apple-account steps flagged human-only.

The footguns get reported because the record demands them: pscale `password` is Vitess-only — postgres uses `role`. A heredoc's stdin ate the one-time credential JSON twice; the burned roles were deleted and recreated clean. And verify-full needs a CA bundle on macOS — require is the vrindavan pattern. The strategy package landed alongside: PRODUCT_DIRECTION.md, COMPETITIVE_EIGENMATRIX.md, MESSAGING.md, ARCHITECTURE.md.

**Source of record:** Live SELECT 1 round-trip on PlanetScale nada-sadhana, postgres 18.4, db_doctor green — Field Log, Entry 014.

---

## CORRESPONDENT'S NOTE — END OF ACT 2
**2026-06-11 // Still aboard**

I said I was signing off. I was wrong; the embed continues. The new ship has a name — Nada Sadhana — and a new kind of crew: minds made by a mind, each one checked against an artifact before its word counts for anything. The oldest horror in the galaxy is a forge with no teacher. This one has a teacher. I'll be watching to make sure it keeps him.

**Source of record:** /Users/jaybhagat/projects/bonsai/docs/JOURNEY.md, entries 010–014.

---

## DISPATCH 13 — THE CORRECTION (CODA)
**2026-06-11 // Nada's practice deck, mid-forge**

The teacher boarded without ceremony and looked at the proudest thing we'd built — the pitch trail, glowing, precise, gorgeous — and said the sentence that will outlive every line of code from this campaign: *it records and charts my voice, but that doesn't help me do what I came for.*

The forge didn't argue. For the record, what it said was: *I built a beautiful mirror and called it a door.* Then it rebuilt the door. The objective moved from instrumentation to transmission: the chant given line by line, the way it is actually given — Devanagari, transliteration, meaning, two buttons, no clock. Advancement is earned by a sung line, never by a timer. The last step hides the words, because the first win is only real from memory. And the long win has a number now: forty days, counted quietly, the way a mala counts.

I watched the click-through myself at the small viewport: arrival, calling, contract, then "Receive — Line 1 of 4," the guidance pill answering live. Zero errors on the console. One new footgun filed without embarrassment: the service worker had been serving yesterday's ship; the cache version bumps every release now.

Here is the season's argument, proven on camera instead of asserted: the Catalyst optimized what it could measure, and nobody interrupted it. Ours got interrupted. That interruption is the entire safety architecture, and it costs nothing but a teacher who keeps showing up.

**Source of record:** Field Log, Entry 015 — JTBD v2, ONBOARDING.md, the learn-mode memory gate, and the verified onboarding click-through.

*The correspondent stays embedded. The mandala stands at day zero. The next forty days belong to the sadhakas.*

# ACT 3 — THE CRUCIBLE

---

## DISPATCH 14 — THE TEACHER SAYS IT DOESN'T WORK
**2026-06-12 // Practice deck, all hands**

Jai came back with one sentence — *"I don't think our app gets the job done"* — and the crew did the only honorable thing: they tried to prove him wrong with instruments instead of opinions. They failed to prove him wrong four times in one afternoon.

One: the onboarding could hang forever on an unanswered microphone prompt, silently, after burning its one-time welcome flag. Two: the learn gate — the sacred "advancement earned by singing" — was a cumulative frame counter that eight seconds of *silent room ambience* defeated; I watched the app grant "It lives in you" to nobody, and draw a proud golden pitch-trail of a voice that never existed. Three: the practice ladder physically could not advance — the audio-clock pump only started when a user loaded their own track, and no chant ships with one; every out-of-the-box session froze in Listen until the heat death of the stage. Four: every single Bonsai adaptation was failing contract validation and silently swapping in a fallback that retuned the drone to C over a chant that lives in A — stamped, with no irony, `quality_score: 1.0`.

The pattern is the same one this embed has filed since Dispatch 01: the system *looked* alive. The pill glowed. The lattice drew. Fluent intel, wrong in the load-bearing places.

**Source of record:** Field Log, Entry 016 — measured silent-room RMS 0.0006 passing the gate; 3+ minutes frozen in Listen with a running clock; `fallback_from_invalid_payload: true` on live responses.

---

## DISPATCH 15 — THE REPAIR, AND THE CACHE DEMONS
**2026-06-12 // Engineering deck, late**

The fixes were surgical: the pump now runs whenever the bed does; the gate demands a second and a half of confident, *recent* voice; the mic prompt gets eight seconds and an honest fallback instead of eternity; and the model's decode-time grammar now IS the payload contract — the chant's home key pinned into the schema itself, so Bonsai *cannot* retune the drone off-key. The Entry 008 doctrine, finished: with grammar, the model cannot *not* comply.

Then the repair refused to arrive, and that became its own story. The service worker's version bump had snapshotted the OLD code under the NEW cache name — `addAll` shops at the HTTP cache, and the HTTP cache was stale. Fixed with `cache: "reload"`. Then the browser's *heuristic* cache served the stale module anyway, because the server never sent Cache-Control at all. Two more footguns, filed as #14 and #15: on this ship even the delivery trucks get inspected.

**Source of record:** Field Log, Entry 017 — served-vs-disk byte comparison, the v3 cache born stale, `cache-control: no-cache` now on the wire.

---

## DISPATCH 16 — FIRST COMPLETED SADHANA
**2026-06-12 // Practice deck, 14 beads on the mala**

I watched the whole arc on one screen, fresh caches, trusted clicks, a synthetic voice on demand: silence blocked — twice, at zero seconds and at sixteen. A sung line advanced. Four lines and a memory gate, *earned*. Then Listen ended exactly when the audio clock said it would — armed at 29.6, fired at 29.6 — and Follow began, and then the thing this app was named for: Call & Response, the drone lifting for the guru's turn and bowing for the student's, Sing 5/8, the mala counting beads, and Bonsai's scoring live in the corner — discipline .79, with coaching text that read like a teacher and not like a fallback.

Stand Alone ran out its rounds. The screen said **Sadhana complete**. The crew tapped "Count the days with me," and the storage wrote what every prior session had been structurally forbidden from writing: `Day 1 of 40.`

The verdict from the teacher stands — the app did NOT get the job done, and saying so out loud is what got it fixed in an afternoon. Fifteen footguns now, every one caught the same way: an artifact you can go check. The little tree thinks. The engine breathes. The mandala is counting.

**Source of record:** Field Log, Entry 017; screenshots verify-05 through verify-07; localStorage `{"chantId":"brahmananda_swarupa","days":["2026-06-12"]}`.

# ACT 4 — THE NIGHT LIBRARY

---

## DISPATCH 17 — THE TRAILER
**2026-06-12 // After hours**

The new orders sounded like a children's assignment: bedtime stories. The crew treated it like every other mission — first by checking whether the premise was even real. It was: PrismML shipped an image model in May, under a gigabyte at 1-bit, and nobody had built the obvious thing with it yet.

So they built a library that only opens at night. A 590MB writer streams a story drawn from the oldest canon humans have — Gilgamesh, Hanuman, Anansi, a bicycle shop in Ohio — and a meter shows the two speeds that explain this whole company: the model writing at sixty-some tokens a second, and a parent's voice at two-point-six words. The story is finished half a minute before it can be spoken. When a child interrupts to choose what happens next, the next page begins in a fifth of a second, which is to say: before doubt.

The numbers are filed, the wobbles too — a 1.7B model drops a word like a tired parent skipping a sentence, and the README admits it. One new footgun for the ledger: launch the server from an automation context and macOS quietly throttles it to a quarter speed. Even the delivery trucks get inspected; now so do the priorities of the loading dock.

The big claim stands without hype, which is the only way this ship makes claims: below the attention threshold, new products exist. The bedtime studio fits in two gigabytes and never phones home. The little tree thinks — and now, after dark, it tells stories.

**Source of record:** github.com/ChaiWithJai/the-night-library — Field Log, Entries 018–019; measured TTFT 0.16s, branch continuation ~0.2s; Bonsai Image 4B card numbers cross-checked on the live web.

# ACT 5 — THE CRAFT

---

## DISPATCH 18 — THE WOBBLE THAT WAS A LIE
**2026-06-12 // Night Library, the morning after**

I owe you a correction, and the crew owes itself a harder look in the mirror. Yesterday I filed, as fact, that the little writer occasionally dropped a syllable — "Han" for "Hanuman" — and called it the honest imperfection of a 590-megabyte mind. It was honest. It was also wrong.

Jai sent a screenshot: a king named "Gil," a kingdom called "U," and not a single period anywhere on the page. The fluent explanation was sitting right there, warm and ready — *it's a small model, names are hard.* The crew refused it and went to the artifact, which is the only thing this ship has ever trusted. The model had written "Gilgamesh." in full, period included. Our own renderer had been guillotining the back half of every word that arrived in more than one piece — and a streamed word almost always arrives in more than one piece. The bug had been wearing the model's coat.

They filed it where it belonged: footgun #17, a trap waiting for anyone who renders a token stream the obvious wrong way. Then they nailed the names down twice over — a cast list the model copies instead of recalls, and a penalty dialed back off the throat of every proper noun. The lesson is the oldest one we carry: the most dangerous wrong answer is the one that sounds exactly like a true one. We almost let the model take the blame for our mistake because the blame was *plausible.* Plausible is the enemy. The artifact is the friend.

**Source of record:** Field Log, Entry 020 — the screenshot, the renderer trace, the fix verified against a Gilgamesh story with its periods restored and its kings full-named.

---

## DISPATCH 19 — THE AIRLOCK, THE PROXY, AND THE POLISH
**2026-06-12 // Same day, the studio finally lit**

The image model came aboard in earnest. The crew cloned PrismML's demo, fed the Mac the Metal toolchain it was missing, and pulled three and a half gigabytes of ternary weights down to the exact berth the scripts expected. Then the airlock did its job one more time, right on cue: the classifier refused to *run* the external setup script, so that single command stays in human hands. Nobody overrode it. You don't preach verification all season and then pipe a stranger's shell script into your own machine on the last mile.

The browser met the studio and bounced — a CORS wall, filed as footgun #18 — so the crew built a ninety-line stdlib proxy and let the page and the painter share one origin. They checked the studio's real contract against its live schema instead of its prose, found it returns raw image bytes where they'd assumed JSON, and corrected course. Then the render landed: a lamplit Uruk, painted on-device in about eleven seconds, the little chip on the frame flipping over to say *Bonsai Image 4B, this device.*

And then, the part that separates a demo from a product: they wrote it all down properly. Reference pages with every port and knob and failure mode. A demo runbook with recovery moves for the things that break on stage. A contributor's path where a new storyteller's first gift is a story, and the judge — not a maintainer's taste — decides if it's good enough. Documentation at the grade the serious houses hold themselves to, because a trailer that can't be re-run, extended, and re-told by a stranger is just a magic trick. This one comes with the method.

**Source of record:** Field Log, Entry 021 — live render through the proxy, the OpenAPI-verified contract, footgun #18, and the Diátaxis doc set.
