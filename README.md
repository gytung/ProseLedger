# ProseLedger

**Natural academic expression through explicit editing rules, conditional memory, and inspectable revisions.**

**DSS5105 Capstone · Group 18 · National University of Singapore**

[Generate or revise in your browser](https://gytung.github.io/ProseLedger/create.html?v=20261030e) · [Language-edit walkthrough](https://gytung.github.io/ProseLedger/writing-demo.html?v=20261030e) · [Archived six-case scores](https://gytung.github.io/ProseLedger/#rounds) · [Architecture](docs/ARCHITECTURE.md)

ProseLedger makes the editing operation visible: **identify a passage-level problem, apply a suitable rule, inspect the exact change, then check whether the candidate preserves meaning and improves expression**. The revision loop controls when to continue. The rules explain what the editor should change. Conditional memory provides historical examples only when their reuse conditions match the current passage.

## Current browser workflow

Open the [browser application](https://gytung.github.io/ProseLedger/create.html?v=20261030e) with your own model API key. Generate a six-section research proposal from a topic and attributed source notes, or supply an existing proposal and revise that exact initial text. No local installation or GPU is needed; inference runs at the selected API provider.

The current browser protocol is **`proseledger-browser-3`**. It uses six shared editorial rules:

| Rule | Intended operation |
|---|---|
| Name the actor and action | Clarify an actor or operation already stated in the text. |
| Use concrete wording | Replace vague framing with existing, supported detail. |
| Remove redundancy | Delete repeated meaning while keeping qualifications. |
| Improve information flow | Make referents and established logical relationships clear. |
| Give sentences a clear focus | Reorganize competing points without losing dependencies. |
| Calibrate claims | Express uncertainty and planned-study status precisely. |

Each rule has an applicability condition, an exception, and illustrative positive and negative examples. These are editorial specifications, not validated results or a recipe for evading AI detectors. The editor does not ban hyphens, passive voice, technical vocabulary, or long sentences. Every changed paragraph in explicit-rule mode must identify its rule and supply exact before/after quotations and a reason. The language-edit view displays that evidence alongside acceptance or rejection.

| Route | Current browser revision policy |
|---|---|
| **Targeted** | Apply the shared editing instructions directly to passages identified by current feedback. |
| **Planner-only** | Inspect the text, formulate a bounded plan, and execute local edits without historical cards. |
| **Memory** | Use the same planner and executor with a frozen catalogue of conditional editing examples. |

**All three browser routes start independently from the same initial draft. There is no shared first revision.** Each can stop when no useful safe edit exists. All receive their own prior-round decision history; only Memory receives historical cards. The reviewer sees anonymous candidate pairs, not branch names, rule explanations, or card labels. Content checks must pass and the reviewer must prefer the candidate to its own preceding draft before the edit is retained.

The browser uses five expression dimensions totaling **0–20 problem severity**. Raw scores are never smoothed to guarantee improvement. Rule counts, accepted edits, and detector probabilities are not quality scores. A card-assisted edit can fail, and an accepted Memory edit may use no historical card. There is no established general Memory advantage.

Draft-only generation uses two model stages; reviewing a supplied draft uses one. Three-round comparison adds at most twelve stages. Transport retries can add HTTP attempts, and context lengths differ across routes. See the [browser guide](docs/BROWSER_DEMO.md) for keys, checkpoints, limitations, and recording instructions.

The [language-edit walkthrough](https://gytung.github.io/ProseLedger/writing-demo.html?v=20261030e) presents a saved run and its actual before/after evidence without making model calls. Live generation remains available in the separate application. A saved walkthrough is not a new generation or a guarantee that another run will reproduce its numbers.

An optional **GPTZero** panel records an external observation for selected text, with a separate GPTZero key and explicit consent. It does not feed the writer, decide retention, or admit memory. Connector tests and a public browser-access preflight are available; an authenticated detector scan is still pending. Human naturalness judgments remain separate from detector authorship estimates.

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
