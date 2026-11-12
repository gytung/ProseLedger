# ProseLedger

**From a research proposal to a checked, traceable revision.**

**DSS5105 Capstone · Group 18 · National University of Singapore**

[Generate a proposal](https://gytung.github.io/ProseLedger/create.html) · [Revise a proposal](https://gytung.github.io/ProseLedger/revise.html) · [Final application](project/README.md) · [Controlled evaluation](project/evaluation/README.md) · [Archived evaluation](https://gytung.github.io/ProseLedger/#rounds)

ProseLedger generates a research proposal from supplied source notes, edits its language section by section, checks the changes against the original and evidence, and retains a revision only when its checks pass. The final manuscript, rejected candidates, repair decisions and exact-text fingerprints remain inspectable.

## Final application and reproducible study

**Start in [`project/`](project/README.md).** This directory contains the current desktop application, Windows and macOS launchers, browser source, attributed examples and reproducible evaluation. The root `app.py`, `proseledger/` and the six-case dashboard preserve the earlier three-route memory experiment. They are an archive, not the entry point for the final section-revision system. The published generation and revision links above use the current browser workflow.

### Run locally from a clean checkout

Install Python 3.10 or later; Python 3.12 is recommended. On Windows, enable **Add Python to PATH**. Then:

```sh
git clone https://github.com/gytung/ProseLedger.git
cd ProseLedger
python project/launch.py verify
python project/launch.py open
```

On macOS, use `python3` if `python` is unavailable. The desktop application uses the Python standard library. Select **Hosted writer** and configure your own model API connection to use it without downloading a local model. Alternatively, use local Qwen for section rewriting and your own API or signed-in official Codex CLI for drafting, review and repair.

| Action | Windows | macOS |
|---|---|---|
| Open the desktop app | `project/Windows/02_Open_ProseLedger.bat` | `project/Mac/02_Open_ProseLedger.command` |
| Optional local Qwen setup | `project/Windows/01_Setup_Local_Qwen.bat` | `project/Mac/01_Setup_Local_Qwen.command` |
| Optional official account login | `project/Windows/03_Login_Codex.bat` | `project/Mac/03_Login_Codex.command` |

Local setup explicitly downloads Ollama and `qwen2.5:7b-instruct-q4_K_M`, approximately 4.7 GB of model weights. We recommend 16 GB RAM and 15 GB free disk space. Opening the app does not download missing model assets. API usage requires the operator's own provider key and credit; account-based review requires the official CLI installed and signed in separately. GPTZero validation is optional and uses a separate API key after manuscript retention.

The public browser route requires no local installation. To serve the same pages from this checkout:

```sh
python -m http.server 8080 --directory docs --bind 127.0.0.1
```

Open `http://127.0.0.1:8080/create.html` or `http://127.0.0.1:8080/revise.html`. The selected model provider must permit browser requests through CORS. See the [application guide](project/README.md) for inputs, downloads, recovery and module responsibilities.

### Inspect or repeat the controlled evaluation

[`project/evaluation/`](project/evaluation/README.md) contains the twelve-case paired study: frozen inputs and code, Generic and Rules outputs, contextual reviews, bounded repairs, decision ledgers, blinded automated comparisons, known-answer challenges and post-retention detector observations. Public human-evaluation records remain separately identified. The study compares editorial instructions with the same local writer and verification procedure; it does not evaluate historical memory retrieval.

For fresh inference, start the pinned local model and configure the recorded reviewer as described in the [evaluation guide](project/evaluation/README.md). Use a new output directory:

```sh
python project/evaluation/reproduce.py --out runs/controlled-rerun --execute
```

This verifies the frozen inputs and creates an independent run without copying archived model responses. Omit `--execute` to prepare and inspect the workspace before making model calls. The separate [`project/research/qwen_mlx/`](project/research/qwen_mlx/README.md) profile preserves the earlier Mac study. MLX, Ollama and visitor-selected cloud models are distinct execution conditions and do not share guaranteed output text or detector values.

## Current browser workflow

The public website has two separate workspaces:

- **[Generate proposal](https://gytung.github.io/ProseLedger/create.html)** takes a topic and two to ten source excerpts and produces one six-section proposal. It does not revise the text. Download the proposal, or select **Continue to revision** to carry that exact text and its sources to the next page.
- **[Revise proposal](https://gytung.github.io/ProseLedger/revise.html)** starts from an existing proposal, rewrites six sections through a cloud model API, then reviews and repairs the changes. The page retains the checked revision or restores the original.

**Both public pages run directly in the browser using the visitor's own model API key. No local installation, Ollama, Codex sign-in or pairing code is required.** Choose OpenAI API, OpenRouter or a compatible provider; enter a Model ID available to that account and the matching API key; then select **Test connection**. Use the provider's HTTPS endpoint when configuring a custom service. The provider must allow browser requests from this website.

Model calls use that provider's API credit. A ChatGPT subscription or Codex account login is not an API key. By default, the selected cloud model handles writing and review in separate calls. The optional section-writer Model ID can select a different model offered by the same provider, using the same key; only the six section rewrites use that model. Cloud Qwen is an option when the chosen provider offers it, but it is not the local Qwen 7B experiment.

**Proposal → six rule-guided section revisions → section review → bounded repairs → whole-document audit → retained manuscript and revision ledger.**

Six editorial rules guide the writer: actor and action, concrete wording, redundancy, information flow, sentence focus and calibrated claims. Scientific content, attribution, uncertainty and planned-work status must be preserved. Citation and number checks supplement the model review. These checks are fallible; they do not establish scientific truth.

Repairs use exact, unique text anchors. At most three non-overlapping patches may cover no more than 35% of a section. The Extended policy permits at most two extra whole-document repair cycles. Retention requires passing checks, no unresolved model findings, a readability judgment of better or similar, and 85–115% of the original word count. Otherwise the original is retained.

The revision page separates **Original, Candidate and Retained**, and provides the manuscript, ledger and full run for download. Save a checkpoint before closing the tab; resume requires unchanged input, policy and model settings. The current ledger records **this run's edits and checks**; it does not retrieve historical cards or train a model. Archived three-route memory experiments remain below.

API keys stay in tab memory, are sent only to the selected provider, and are excluded from exports. **Continue to revision** temporarily transfers only the topic, source excerpts and proposal through this tab's session storage, then removes that transfer record on arrival. Enter the API key again on the revision page. Requests go from the browser to the provider; GitHub Pages does not run a model or supply a shared account.

**GPTZero is optional and separate.** After revision, any teammate can manually enter their own or the team-shared GPTZero API key to scan the exact original and retained text. Observations include text hashes and timestamps. They do not select edits or alter the manuscript. Class probabilities are not the proportion of AI-written words, a naturalness score or a guarantee of factual accuracy.

The independently distributed local experiment package remains a separate option for local Ollama Qwen rewriting and account-based review. Its setup is not required for these public pages. Archived Mac results, the local package and a current cloud run can differ in draft, model, runtime, sampling and detector version. Report each new run with its own record and exact-text validation; no fixed score decrease is promised. See [local-experiment context](docs/OLLAMA_BROWSER.md).

See [the workspace guide](docs/REVISION_WORKSPACE.md) for setup, recovery and recording. Earlier [language-edit recordings](https://gytung.github.io/ProseLedger/writing-demo.html) belong to the archived comparison editor.

## Archived Python evaluation

The Python application and its frozen six-case evaluation use a **different protocol**: shared first Targeted revision, a 30% rule / 70% model composite score, and non-worsening selection. They remain available for reproducibility. Do not use their scores as measurements of the current browser editor or combine their means with new browser runs.

The earlier [two-minute archived walkthrough](https://gytung.github.io/ProseLedger/presentation.html) displays those six recorded cases and makes no model calls. The archived presentation and this page use the same `evidence.json`. See the [earlier recording script](docs/RECORDING_GUIDE.md).

Open the **[round-by-round dashboard](https://gytung.github.io/ProseLedger/#rounds)**, or download and open `docs/index.html` locally. It contains all six recorded cases, their initial and retained texts, and the decision traces. No installation, credentials or model calls are required for this viewer.

The dashboard shows the initial score (round 0), all three revision rounds, batch means and per-case curves. Candidate scores and retained-draft scores are shown separately so rejected edits remain visible. The complete [round-score CSV](docs/round_scores.csv) contains 18 initial entries and all 54 branch decision records.

The viewer inspects saved results. It does not rerun the algorithm or generate new text. The same six-case data power the archived evaluation presentation.

| Case | Initial | Targeted | Planner-only | Memory |
|---|---:|---:|---:|---:|
| 01 Research handoff | 10.5 | 9.1 | 9.1 | 9.1 |
| 02 Citation identity | 9.1 | 6.3 | 6.3 | 7.0 |
| 03 Ablation rationale | 8.4 | 5.6 | 6.3 | 6.3 |
| 04 Resource comparison | 7.0 | 7.0 | 7.0 | 7.0 |
| 05 Negative evidence | 7.0 | 7.0 | 7.0 | 7.0 |
| 06 Terminology alignment | 8.4 | 6.3 | 6.3 | 6.3 |
| **Mean** | **8.4000** | **6.8833** | **7.0000** | **7.1167** |

Lower scores indicate fewer measured writing-style problems. Memory versus Targeted: **0 wins, 4 ties, 2 losses**. These results do not establish a memory advantage. The preservation checks are automated, and the style score is not a human preference or authorship probability. See [evaluation notes](docs/EVALUATION.md).

## Run the archived-protocol Python application

Use **Python 3.12**. From the repository root:

```bash
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# macOS or Linux
source .venv/bin/activate
```

Install dependencies, verify resources, and open the local application:

```bash
python -m pip install -r requirements.txt
python -m proseledger verify
python -m streamlit run app.py
```

The application provides new proposal generation, the saved six-case evaluation, and inspection of the memory catalogue. The public source package does not bundle Python, a model executable or a signed-in account.

### Model access

The Python application's model transport uses **OpenAI Codex CLI**. Install and authenticate it using the [official CLI instructions](https://developers.openai.com/codex/cli/). The CLI must be on `PATH`; alternatively set `PROSELEDGER_CODEX_PATH` to its executable path. Generation requires network access and an account with access to the configured model. No local model training or GPU is required.

The recorded evaluation used `gpt-6.1-sol`. The runtime retains that model contract. Fresh model outputs can differ even when the topic and sources are unchanged.

### Command-line generation

```bash
python -m proseledger run --sources data/sources.json --topic "Evidence-preserving revision of research proposals" --output runs/example
```

To resume an interrupted run, repeat the same command with `--resume`. Keep its model, topic, sources and output folder unchanged. Completed response records are reused; unfinished work may make new calls. Use a new output directory for a new experiment.

The CLI exports the initial proposal, all three retained proposals, checks, scores and per-round decisions. Runtime outputs are local and ignored by Git. They may contain supplied source text and application requests; review them before sharing.

## Design

```text
Generate proposal page
  topic + sources → selected cloud API → one proposal → download / transfer

Revise proposal page
  existing proposal + sources → six rule-guided cloud-model rewrites
    → separate model review → bounded repair → whole-document audit
    → retain candidate or original → manuscript + per-run revision ledger
    → optional, separate GPTZero observations
```

Generation and revision are explicit operations. The handoff reuses the generated draft without regenerating it. Draft generation alone does not imply that a proposal has passed the revision checks.

The original Python drafting graph, three-route memory comparison and frozen scores are documented separately in [architecture](docs/ARCHITECTURE.md). The archived memory mechanism is a writing-specific adaptation of verifier-aware memory governance, not a reproduction of every MemGuard component or benchmark.

## Repository map

```text
app.py                 Local application entry point
proseledger/           Drafting, revision, checking and model transport
ui/                    Background job support
data/                  Frozen catalogue and attributed example source notes
docs/assets/           Browser generation/revision engine, rules and model transports
docs/local/            Archived optional connector bundle; not used by public pages
docs/                  Live UI, saved walkthroughs, archived evidence and documentation
tests/                 Offline checks; no paid model calls
scripts/               Publication and resource checks
```

See [architecture](docs/ARCHITECTURE.md), [reproducibility](docs/REPRODUCIBILITY.md) and [publishing instructions](docs/PUBLISHING.md).

## Development checks

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
node --test tests/*.test.mjs
python scripts/check_publication.py
```

The test suite checks contracts and recorded-data consistency without generating a new proposal. Test success is not evidence of better writing quality or a successful live account configuration.

## Attribution and licensing

The Python drafting components adapt the MIT-licensed [LiRA implementation](https://github.com/lira-workflow/auto-review-writing). The project adds course-specific integration and revision control; it does not claim that the reused drafting graph was developed from scratch. The original notice is retained at `proseledger/drafting/LICENSE`.

The memory design is inspired by [MemGuard](https://arxiv.org/abs/2608.21867). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for component provenance and the separate licensing of source excerpts. Code is provided under the [MIT License](LICENSE); that license does not relicense third-party paper excerpts.

## Team

Developed for the **DSS5105 Capstone, Group 18**, at the **Department of Statistics and Data Science, National University of Singapore**.

| | Member |
|---|---|
| 1 | Jiuxing Li |
| 2 | Bill Guangyuan Dong |
| 3 | Zhengqi Feng |
| 4 | Alexander Lim Han Yang |
| 5 | Diqing Xu |
| 6 | Zhu Sijin |

**Supervisor:** Tan Tian Huat.
