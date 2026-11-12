# ProseLedger

Evidence-grounded proposal writing and verified language revision.

DSS5105 Capstone · Track 3 · Group 18 · National University of Singapore

ProseLedger generates a research proposal from attributed source excerpts, or revises an existing proposal. Six explicit editorial rules guide section-level rewriting. Content review, bounded repairs and document-level checks determine which text is retained. Each run exports the manuscript and an inspectable revision ledger.

## Choose an interface

| Interface | Requirements | Writing and review |
|---|---|---|
| [Generate proposal](https://gytung.github.io/ProseLedger/create.html) and [Revise proposal](https://gytung.github.io/ProseLedger/revise.html) | Browser; your compatible model API key and credit | Direct requests from your browser to your provider |
| Desktop app | Python 3.10+; Windows 10/11 x64 or macOS | Local Qwen through Ollama, or an explicitly selected hosted writer; separate review connection |
| MLX research profile | Apple Silicon Mac, Python 3.12 and Node.js 20+ | Pinned Qwen2.5 7B MLX writer and hosted review; archived study inputs and outputs |

The browser does not require a connector, Ollama or downloaded weights. API billing and access are separate from ChatGPT subscription access. Optional GPTZero validation uses its own API key and credit.

## Desktop quick start

1. Install [Python](https://www.python.org/downloads/) 3.10 or later; 3.12 is recommended. On Windows, enable **Add Python to PATH**. Extract this complete source folder to a short path, such as `C:\ProseLedger`.
2. For local writing, double-click `Windows/01_Setup_Local_Qwen.bat` or `Mac/01_Setup_Local_Qwen.command`. This explicitly downloads the pinned Ollama runtime and `qwen2.5:7b-instruct-q4_K_M` model. The model is approximately 4.7 GB; allow 16 GB RAM and 15 GB free disk space. CPU-only writing can take tens of minutes. Skip this step for hosted writing.
3. Double-click `Windows/02_Open_ProseLedger.bat` or `Mac/02_Open_ProseLedger.command`. The app opens a loopback-only browser interface. Keep its console open. No Python packages or administrator access are required by the application.
4. Select **Local Qwen** or **Hosted writer**. Configure the review connection: OpenAI Responses, a compatible Chat Completions service, or your own signed-in official Codex CLI. API mode needs a base URL, Model ID and matching API key. Codex mode requires the official CLI installed separately; use `03_Login_Codex` after installation. If necessary, set `PROSELEDGER_CODEX_PATH` to its executable. No credentials are bundled.
5. Test the connection. Load the included example or supply a topic and 2–10 attributed source excerpts. Choose initial generation or supply an existing six-section manuscript, then start the run.
6. Inspect **Original**, **Candidate before selection** and **Retained**. Download the manuscript and all records. Records stay under `runs/`; interrupted runs can resume with the same inputs, models and policy.

Command-line equivalents from this folder:

```sh
python launch.py setup
python launch.py open
```

On macOS, use `python3` when `python` is unavailable. Setup is the only launcher that downloads missing Qwen assets. Open restarts already installed local assets without downloading. For API-only use, select **Hosted writer** in the app. macOS 14+ and Windows 10 22H2/11 are required for the pinned local Ollama runtime. The source application itself uses the Python standard library.

## Browser workflow

Select a provider, enter your own API key and Model ID, and test the connection. On **Generate proposal**, enter a topic and source excerpts. **Continue to revision** transfers the exact generated proposal and evidence to the revision page; it does not transfer the API key. Re-enter the key there, choose the repair policy and start revision. Download the final draft, complete run record and revision ledger.

The main model performs generation, review and repair. Under advanced API settings, an optional section-writer Model ID can select a different writer available through the same provider and key. Leaving it blank uses the main model. The browser route does not use a ChatGPT login or a local Qwen service.

To serve these pages from a clean checkout:

```sh
python -m http.server 8080 --directory docs --bind 127.0.0.1
```

Open `http://127.0.0.1:8080/create.html` or `http://127.0.0.1:8080/revise.html`. The provider must permit browser requests through CORS. Do not open the pages directly as `file://` documents.

## Optional GPTZero observation

After revision, enter your GPTZero API key in the validation panel and consent to sending the original and retained manuscript. Inspect both results, then download the detector observations. The desktop also imports completed run archives so one operator can scan teammates' outputs. Credentials are not included in exports.

Detection is performed after candidate retention. Its result does not guide the edit or determine retention. GPTZero AI-class probability is an authorship-pattern estimate, not a proportion of AI-written words and not a measure of factual correctness or human preference.

## Implemented method

The writer applies six rules: explicit actor and action; concrete wording supported by the source; removal of redundant phrasing; information flow; sentence focus; and calibrated scientific claims. It may change expression but must preserve evidence, citation identity, numbers, scope, uncertainty and planned-study status.

Section review is followed by exact, bounded repair: at most three non-overlapping patches per section, covering at most 35% of the candidate section's matched text. A final audit assesses the assembled proposal. Retention requires passing the configured guards, no unresolved audit findings, readability judged no worse and a final length within 85–115% of the original. Otherwise the original is retained. The extended policy permits at most two further full-document repair cycles.

The ledger preserves verification signals and decisions within the current run, adapting a MemGuard-inspired governance principle. The production workflow does not retrieve historical experience cards. Its results therefore do not establish a cross-task memory benefit. The original MLX study and any fresh browser or Ollama run must be reported as separate execution configurations.

## Module map

| Location | Responsibility |
|---|---|
| `app/core.py` | Desktop editorial rules, orchestration, guards, bounded repairs and retention |
| `app/transport.py` | Local Qwen, official CLI and model API clients; GPTZero requests |
| `app/server.py`, `app/run_import.py`, `app/web/` | Loopback UI, history, safe run import and export |
| `docs/create.html`, `docs/revise.html` | Public generation and revision workspaces |
| `docs/assets/revision-engine.js` | Browser protocol, checks, checkpoints and retention |
| `docs/assets/api-client.js`, `external-validation.js` | Browser model transport and separate detector observations |
| `docs/assets/revision-app.js`, `revision.css` | Browser interaction and presentation |
| `tools/local_qwen.py`, `platform/local_runtime_sources.json` | Explicit setup, pinned downloads and local model readiness |
| `examples/` | Attributed input excerpts and sample proposal |
| `research/qwen_mlx/` | Apple Silicon research runners, frozen inputs and recorded outputs |
| `evaluation/` | Frozen paired study, all responses and outputs, detector observations and reproducible analysis |
| `report_figures/` | Reproducible vector figures and documented strategic assumptions; no model calls |
| `tests/` | Workflow, import, transport, checkpoint and browser contracts |
| `PACKAGE_MANIFEST.json` | File checksums for the distributed source |

## Verify the source

```sh
python launch.py verify
python -m unittest discover -s tests -p "test_*.py"
npm test
```

Node.js 20+ is needed for JavaScript tests, not the desktop application. Optional browser tests require their development dependency:

```sh
npm install
npx playwright install chromium
npm run test:browser
```

Software tests use synthetic responses and do not measure model quality. Research rerun commands and model identity are documented in `research/qwen_mlx/README.md`. Fresh generations are stochastic and service-dependent; checksummed archived records reproduce the reported observations, while new inference produces a new experimental record.

## Controlled evaluation

`evaluation/` records twelve frozen proposals, each processed by generic copy-editing and the six-rule writer using the same local Qwen configuration and verifier. All outputs and automated comparisons are retained. `evaluation/human/` contains separately sanitized response summaries from the team’s human evaluation; those responses are not part of the twelve-case experiment.

To create an independent execution without importing archived model responses:

```sh
cd evaluation
python reproduce.py --out ../fresh-evaluation --execute
```

First start the pinned model and configure the review connection as described in `evaluation/README.md`. The destination must not exist. GPTZero scans are a separate command requiring your detector key. Recorded probabilities describe classifier responses; they are not measures of human authorship or proof of writing quality. The study compares editing instructions under controlled inputs, not historical memory retrieval.

## Team

Jiuxing Li; Bill Guangyuan Dong; Zhengqi Feng; Alexander Lim Han Yang; Diqing Xu; Zhu Sijin.

Supervisor: Tan Tian Huat. Department of Statistics and Data Science, National University of Singapore.

See `LICENSE` and `THIRD_PARTY_NOTICES.md` for code, model and source-excerpt attribution.
