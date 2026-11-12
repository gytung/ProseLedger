# ProseLedger

**From a research proposal to a checked, traceable revision.**

**DSS5105 Capstone · Group 18 · National University of Singapore**

[Generate a proposal](https://gytung.github.io/ProseLedger/create.html) · [Revise a proposal](https://gytung.github.io/ProseLedger/revise.html) · [Usage and limits](docs/REVISION_WORKSPACE.md) · [Archived evaluation](https://gytung.github.io/ProseLedger/#rounds) · [Architecture](docs/ARCHITECTURE.md)

ProseLedger generates a research proposal from supplied source notes, edits its language section by section, checks the changes against the original and evidence, and retains a revision only when its checks pass. The final manuscript, rejected candidates, repair decisions and exact-text fingerprints remain inspectable.

## Current browser workflow

The public website has two separate workspaces:

- **[Generate proposal](https://gytung.github.io/ProseLedger/create.html)** takes a topic and two to ten source excerpts and produces one six-section proposal. It does not run Qwen or revise the text. Download the proposal, or select **Continue to revision** to carry that exact text and its sources to the next page.
- **[Revise proposal](https://gytung.github.io/ProseLedger/revise.html)** starts from an existing proposal. Local **Ollama Qwen2.5 7B** rewrites six sections; the visitor's **Codex account** reviews and repairs the changes. The page retains the checked revision or restores the original.

The default connection uses a [local connector](https://gytung.github.io/ProseLedger/local/ProseLedger_Local_Connector.zip). Extract it, open **Start_Windows.bat** or **Start_Mac.command**, and choose the full setup (or proposal-only setup if you do not need revision). Complete Codex sign-in locally, then paste its **pairing code** into the website. The pairing code is not an API key. Generation needs only the Codex connector; revision also needs Ollama with **`qwen2.5:7b-instruct-q4_K_M`**. The first full setup downloads the runtime and approximately 4.7 GB of model weights; existing project model files can be reused. Use the address printed by your launcher (normally Ollama port `11436`) and click the connection tests. The website cannot install or start local programs for you.

No Qwen cloud credit is needed when using local Ollama. Codex account access and usage limits still apply. Cloud API mode remains optional: it requires the selected provider's own API key and API credit. This API billing is separate from a ChatGPT subscription. Hosted section writing is available in API mode; it is a different execution configuration from the local Qwen route.

**Proposal → six local section revisions → Codex section review → bounded repairs → whole-document audit → retained manuscript and revision ledger.**

Six editorial rules guide the writer: actor and action, concrete wording, redundancy, information flow, sentence focus and calibrated claims. Scientific content, attribution, uncertainty and planned-work status must be preserved. Citation and number checks supplement the model review. These checks are fallible; they do not establish scientific truth.

Repairs use exact, unique text anchors. At most three non-overlapping patches may cover no more than 35% of a section. The Extended policy permits at most two extra whole-document repair cycles. Retention requires passing checks, no unresolved model findings, a readability judgment of better or similar, and 85–115% of the original word count. Otherwise the original is retained.

The revision page separates **Original, Candidate and Retained**, and provides the manuscript, ledger and full run for download. Save a checkpoint before closing the tab; resume requires unchanged input, policy and model settings. The current ledger records **this run's edits and checks**; it does not retrieve historical cards or train a model. Archived three-route memory experiments remain below.

Connection secrets stay in tab memory and are excluded from exports. The Codex pairing code is sent only to the local connector; no cloud credentials are sent to Ollama. **Continue to revision** temporarily transfers only the topic, source excerpts and proposal through this tab's session storage, then removes that transfer record on arrival.

**GPTZero is optional and separate.** After revision, any teammate can manually enter their own or the team-shared GPTZero API key to scan the exact original and retained text. Observations include text hashes and timestamps. They do not select edits or alter the manuscript. Class probabilities are not the proportion of AI-written words, a naturalness score or a guarantee of factual accuracy.

The pinned Ollama writer does not make a visitor's run a reproduction of an archived Mac result. Draft, runtime, review model, sampling and detector version can differ. A new result must be reported with its own run record and exact-text validation; no fixed score decrease is promised.

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
  topic + sources → Codex (or chosen API) → one proposal → download / transfer

Revise proposal page
  existing proposal + sources → six rule-guided local Qwen rewrites
    → Codex section review → bounded repair → whole-document audit
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
docs/local/            Local Codex connector and Ollama launchers
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
