# Bonsai Workbench

Bonsai Workbench is a private local agent for research and creative work. You
describe the result you want. The Workbench chooses a configured local
capability, shows the work as it happens, checks the result, and keeps your
decision with the artifact.

The current app can search local sources, write cited answers, create HTML
pages, and generate images. The next product journey will turn an approved
creative brief into treatments, storyboards, narration, timelines, and finished
films.

[![Agent checks](https://github.com/ChaiWithJai/the-little-tree-thinks/actions/workflows/agent-checks.yml/badge.svg)](https://github.com/ChaiWithJai/the-little-tree-thinks/actions/workflows/agent-checks.yml)

![Bonsai Workbench Day 0](docs/evaluation/assets/bonsai-journey-arrival.png)

## What works today

| Job | Current path | Status |
|---|---|---|
| Search private project files | Built in lexical index | Verified |
| Write a cited answer | Ternary Bonsai 27B MLX through LM Studio | Verified on the reference Mac |
| Create a responsive HTML page | Qwen 3.5 2B Q4 through llama.cpp | Verified |
| Create a local image | Bonsai Image 4B ternary MLX demo | Verified on the reference Mac |
| Keep runs and reviews | SQLite in `.bonsai-agent/` | Verified |
| Recover a draft or completed run | Local draft URLs and server run URLs | Verified |
| Produce a treatment, storyboard, and film | Typed creative artifact journey | Planned |
| Generate narration | Liquid LFM2.5 Audio adapter | Planned |
| Compare local and remote image candidates | Provider comparison view | Planned |

The storyboard button in the current app still routes to HTML generation. It
does not yet create typed scenes, shots, audio, or a timeline. The
[creative journey brief](docs/roadmap/STORYBOARD_TO_FILM_JOURNEY.md) defines the
next implementation. Track delivery in
[GitHub issue 5](https://github.com/ChaiWithJai/the-little-tree-thinks/issues/5).

## Day 0

### 1. Install the small app dependency

You need Python 3.11 or newer. Node 18 or newer is only required for the browser
state test.

```bash
git clone https://github.com/ChaiWithJai/the-little-tree-thinks.git
cd the-little-tree-thinks

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

### 2. Create your local config

```bash
cp bonsai_agent.config.example.json bonsai_agent.config.json
```

The local config is ignored by Git because it can contain private source paths.
Edit the file and add at least one source folder under `corpora`.

```json
{
  "corpora": {
    "project": [
      "/Users/you/projects/your-project/docs"
    ]
  }
}
```

You can rename `project`. Corpus names may contain lowercase letters, numbers,
underscores, and hyphens.

### 3. Choose the first runtime

The quickest model backed path is the small HTML runtime. Start an
OpenAI compatible llama.cpp server with the configured model:

```bash
llama-server \
  -m /absolute/path/to/Qwen3.5-2B-Q4_K_M.gguf \
  --host 127.0.0.1 \
  --port 8080 \
  --ctx-size 8192
```

The Workbench can start without a model, but generation waits until the matching
runtime is ready. You can configure the text and image paths later.

### 4. Index your private sources

```bash
python3 bonsai_agent.py index
python3 bonsai_agent.py search "What promise does this project make?"
```

The index uses local lexical scoring, so it does not need an embedding model.
The generated index stays in `.bonsai-agent/index.json`.

### 5. Start the Workbench

```bash
python3 bonsai_agent_web.py
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765).

On the first screen, you can describe a result in your own words or choose a
starter journey. The app will show one of three current paths:

1. Research and cited synthesis from indexed sources.
2. A self contained HTML page with a sandboxed preview.
3. A local image from Bonsai Image 4B.

The result view keeps the plan, observed events, artifact, evidence, and your
review in one place.

## Runtime support

The Workbench uses separate runtimes because each one has a clear job. This also
lets a user run only the models that fit the machine and privacy policy.

### Built in retrieval and storage

| Component | Setup | Why it exists |
|---|---|---|
| Lexical retrieval | No service required | Private search still works when embeddings fail |
| SQLite | Included with Python | Runs, jobs, traces, and reviews survive a server restart |
| Local files | Configured corpus folders | Source material remains on the machine |

### Text synthesis

| Setting | Default |
|---|---|
| Server | LM Studio OpenAI compatible API |
| URL | `http://127.0.0.1:1234/v1` |
| Model | `ternary-bonsai-27b-mlx` |
| Request path | `/completions` |
| Purpose | Cited answers from retrieved local evidence |

Start LM Studio on loopback and load the configured model:

```bash
lms server start --bind 127.0.0.1 -p 1234
lms load ternary-bonsai-27b-mlx
```

The agent uses a completion prompt with a closed reasoning block. This is the
verified local route for the installed 27B MLX model. The generic Bionic tool
session and the Workbench completion route are separate paths.

### HTML generation

| Setting | Default |
|---|---|
| Server | llama.cpp OpenAI compatible API |
| URL | `http://127.0.0.1:8080/v1` |
| Model | `Qwen3.5-2B-Q4_K_M.gguf` |
| Time limit | 40 seconds |
| Output limit | 1,600 tokens |
| Purpose | Fast local page drafts before deterministic checks |

The small model receives a page contract from
`evals/html-distillation.json`. The app checks the result for completeness and
design requirements. If the model fails the contract, the app retains the
failed attempt in the trace and shows a deterministic recovery page.

### Image generation

| Setting | Default |
|---|---|
| Runtime | PrismML Bonsai Image demo |
| Model | Bonsai Image 4B ternary MLX |
| Invocation | Local Python subprocess |
| Network | `HF_HUB_OFFLINE=1` |
| Purpose | Private visual candidates with retained seeds |

Set `image.demo_dir` in the local config or use:

```bash
export BONSAI_IMAGE_DEMO_DIR="/absolute/path/to/bonsai-image-demo"
```

The configured demo must contain its Python environment, generation script,
model weights, pipeline, and bundled VAE. The Workbench refuses to claim that
the image path is ready when any of those parts are missing.

### Known limited paths

1. Bionic embeddings are optional. The tested Bionic installation was missing
   its packaged embedding worker, so the agent uses lexical retrieval.
2. The 27B GGUF did not load in stock llama.cpp because that runtime did not
   support the model tensor format. The verified text path uses MLX.
3. Vision analysis is not an active Workbench capability.
4. Liquid narration was proven in the sibling film production, but no Liquid
   adapter exists in this app yet.
5. OpenAI image generation was used as a production comparison path, but remote
   provider calls are not enabled in the Workbench.

The [local runtime evidence](docs/BIONIC_LOCAL_REVERSE_ENGINEERING.md) contains
the exact failures and tested workarounds.

## Machine requirements

### App development and retrieval

The HTTP app, SQLite store, tests, and lexical retrieval do not require a GPU.
They run anywhere Python and Node are available. Memory use grows with the
number and size of indexed files.

### Small HTML model

The configured 2B Q4 model is the lightest current model path. Required memory
depends on the llama.cpp build, context size, and model file. An 8 GB machine is
a practical starting point, but this repository does not claim a measured
minimum.

### Full local model suite

The verified reference host is:

| Part | Reference |
|---|---|
| Computer | MacBook Pro |
| Chip | Apple M4 Pro |
| CPU cores | 12 |
| Unified memory | 24 GB |
| Operating system | macOS 26.5 on arm64 |

The 27B MLX text model and Bonsai Image use unified memory and device
acceleration. The current scheduler allows one model job at a time. Do not run
text and image generation together until a memory and latency test proves that
the machine has enough capacity.

Model weights live outside this repository and require several gigabytes of
disk. Keep enough free space for model caches, generated media, and SQLite WAL
files.

## Configuration

The JSON file contains model defaults and corpus paths. Environment variables
can override settings without changing the file.

| Variable | Purpose |
|---|---|
| `BONSAI_AGENT_CONFIG` | Use a different JSON config file |
| `BONSAI_TEXT_BASE_URL` | Override the text API URL |
| `BONSAI_TEXT_MODEL` | Override the text model ID |
| `BONSAI_EMBEDDING_MODEL` | Override the optional embedding model ID |
| `BONSAI_HTML_BASE_URL` | Override the HTML API URL |
| `BONSAI_HTML_MODEL` | Override the HTML model ID |
| `BONSAI_IMAGE_DEMO_DIR` | Override the local image demo path |
| `BONSAI_HOST` | Web server bind address. Default is `127.0.0.1` |
| `BONSAI_PORT` | Web server port. Default is `8765` |
| `BONSAI_STATE_DIR` | Local index, database, image, and preview folder |
| `BONSAI_HARNESS_DB` | SQLite database path |
| `BONSAI_CASES_PATH` | Evaluation case catalog path |
| `BONSAI_MAX_CONCURRENT_RUNS` | Concurrent model jobs. Default is `1` |

See [harness architecture](docs/HARNESS_ARCHITECTURE.md) for the complete
process settings.

## State and recovery

The URL tells you which state can be recovered:

| Route | Stored by | Meaning |
|---|---|---|
| `/` | Browser | A clean Day 0 screen |
| `/draft/:id` | Browser local storage | An unfinished private request |
| `/jobs/:id` | SQLite job record | Submitted or interrupted work |
| `/runs/:id` | SQLite run record | A retained result and review |

The server records explicit states instead of asking the browser to guess from
elapsed time. A retry creates a new job and leaves the old evidence intact.

## Repository map

```text
bonsai_agent.py                 Local CLI and model adapters
bonsai_agent_web.py             Loopback HTTP API
bonsai_harness/                 State, persistence, evaluation, and tracing
web/                            Day 0 interface
evals/                          Cases, page presets, and design distillation
tests/                          Python and browser state contracts
scripts/                        Profiling, benchmark, and export tools
docs/                           Active product and architecture documents
docs/evaluation/                Creative agent evidence and target treatments
docs/decisions/                 Accepted architecture decisions
docs/roadmap/                   Work that has a defined product contract
archive/field-study-v1/         Preserved DevRel field study and demo history
```

## Verify the repository

```bash
python3 -m unittest discover -s tests -v
node --check web/app.js
node tests/test_fsm.js
python3 scripts/validate_creative_evaluation.py
```

To capture a local workload profile:

```bash
python3 scripts/profile_harness.py
```

To run model backed benchmark cases without starting new image work:

```bash
python3 scripts/benchmark_bonsai_local.py \
  --html 6 \
  --image 0 \
  --output output/benchmarks/bonsai-local.json
```

## Privacy and security

The server binds to `127.0.0.1` by default. Source files, indexes, runs, reviews,
and generated media remain local. HTML previews use a restrictive content
security policy and cannot load remote assets.

Do not expose the server on another interface. A non loopback deployment needs
authentication, request origin protection, path redaction, and a separate
security review.

## Product documents

Start with these documents:

1. [Day 0 experience](docs/DAY_ZERO_UX.md)
2. [Harness architecture](docs/HARNESS_ARCHITECTURE.md)
3. [Execution state proposal](docs/RFC_AGENT_HARNESS.md)
4. [Creative artifact graph](docs/evaluation/RFC-0002-CREATIVE-ARTIFACT-GRAPH.md)
5. [Creative evaluation and proof](docs/evaluation/README.md)
6. [Repository transition decision](docs/decisions/0001-reframe-around-the-creative-agent.md)

The original DevRel field study remains available in the
[field study archive](archive/field-study-v1/README.md). It is historical
evidence and is no longer the repository entry point.
