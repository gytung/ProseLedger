# ProseLedger

**From a research proposal to a checked, traceable revision.**

**DSS5105 Capstone · Group 18 · National University of Singapore**

[Open the writing workspace](https://gytung.github.io/ProseLedger/create.html) · [Usage and limits](docs/REVISION_WORKSPACE.md) · [Archived evaluation](https://gytung.github.io/ProseLedger/#rounds) · [Architecture](docs/ARCHITECTURE.md)

ProseLedger generates a research proposal from supplied source notes, edits its language section by section, checks the changes against the original and evidence, and retains a revision only when its checks pass. The final manuscript, rejected candidates, repair decisions and exact-text fingerprints remain inspectable.

## Current browser workflow

Open **[create.html](https://gytung.github.io/ProseLedger/create.html)** and enter your own model-provider API key. Supply a topic and two to ten source notes, or bring an existing six-section proposal. Choose **Generate and revise** to run the complete workflow:

**Initial proposal → six section revisions → section review → bounded repairs → whole-document audit → retained manuscript and revision ledger.**

Six editorial rules guide the writer: actor and action, concrete wording, redundancy, information flow, sentence focus, and calibrated claims. The writer must preserve scientific content, source attribution, uncertainty, and planned-work status. The application checks citation identifiers and numbers in addition to the model review. These checks are fallible and do not establish scientific truth.

Repairs use exact, unique text anchors. At most three non-overlapping patches may cover no more than 35% of a section. The extended policy permits at most two additional whole-document repair cycles. The final candidate must pass the checks, have no unresolved model findings, receive a readability judgment of better or similar, and remain within 85–115% of the initial word count. Otherwise the original is retained.

The page shows **Original, Candidate and Retained** separately. A returned original is not presented as an improved rewrite. Download the manuscript, ledger and complete run record. Save a checkpoint before closing the tab; unchanged input, policy and model settings are required to resume validated stages.

The browser runs the workflow; the selected provider runs the model. **No local model, GPU, Python installation or project server is needed.** API billing is separate from a ChatGPT subscription. Credentials stay in tab memory, are sent only to the chosen provider, and are excluded from application exports. A custom provider must permit browser requests. An optional section-writer Model ID can route the six rewriting calls to another model offered by the same provider; generation, review and repair use the main model.

The current revision ledger records **this run's edits and checks**. It does not retrieve historical experience cards or train a model. The older three-route memory experiments remain archived below. The public browser adaptation is also separate from the desktop local-Qwen execution profile; its outputs and latency are not reproductions of the Mac experiments.

**GPTZero is optional and separate.** After the manuscript is retained, a visitor may provide their own GPTZero key to scan the exact original or retained text. Detector observations include text hashes and timestamps. They do not select edits or alter the manuscript. Class probabilities are not the proportion of words written by AI, a naturalness score, or a guarantee of factual accuracy. No fixed score decrease is promised.

See [the current workspace guide](docs/REVISION_WORKSPACE.md) for installation-free use, checkpoint recovery and recording guidance. Earlier [language-edit recordings](https://gytung.github.io/ProseLedger/writing-demo.html) belong to the archived comparison editor and do not describe new runs from this workspace.

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
Topic + source notes → generate a proposal ─┐
Supplied six-section proposal ───────────────┴→ one initial draft (D0)
                                                |
                                    diagnose anchored expression issues
                                                |
                         shared conditional editing rules
                           /                    |                   \
                      Targeted             Planner-only         Memory + cards
                           \                    |                   /
                            bounded edits with exact rule evidence
                                                |
                                 content checks + blind paired review
                                                |
                                     retain / reject / stop
                                                |
                                  branch-local decision records
```

This diagram describes the current browser implementation. A card application must bind to a real changed paragraph and quote evidence that its conditions hold. Cross-document cards remain frozen. Branch history informs later decisions but does not automatically become a new card. The public browser demo has no training or cross-visitor learning.

The original Python drafting graph, fallback routes, and archived score are documented separately in [architecture](docs/ARCHITECTURE.md). The memory mechanism is a writing-specific adaptation of verifier-aware memory governance, not a reproduction of every MemGuard component or benchmark.

## Repository map

```text
app.py                 Local application entry point
proseledger/           Drafting, revision, checking and model transport
ui/                    Background job support
data/                  Frozen catalogue and attributed example source notes
docs/assets/           Current browser editor, rule specifications and transport
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
