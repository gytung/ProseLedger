# ProseLedger

**Research-proposal revision with conditional experience reuse and inspectable decisions.**

**DSS5105 Capstone · Group 18 · National University of Singapore**

[Two-minute walkthrough](https://gytung.github.io/ProseLedger/presentation.html) · [Generate in your browser](https://gytung.github.io/ProseLedger/create.html) · [Recorded round scores](https://gytung.github.io/ProseLedger/#rounds) · [Architecture](docs/ARCHITECTURE.md)

ProseLedger turns a research topic and supplied source notes into a six-section proposal, then compares three revision routes. It separates expression quality from content-preservation checks and records both retained and rejected candidates.

| Route | Revision policy |
|---|---|
| **Targeted / Framework 1** | Rewrite from specific feedback. |
| **Planner-only** | Plan bounded edits, without historical experience cards. |
| **Memory / Framework 2** | Use the same planner and executor with a frozen catalogue of condition-bound editing experience. |

Planner-only and Memory both use their own prior-round feedback. All routes share the initial draft and the first Targeted revision. Later planning decisions choose a local edit, an ordinary targeted rewrite, or a stop. Additional planning calls mean that equal revision opportunities are not equal token budgets.

## Explore the recorded evaluation

For a presentation recording, use the **[two-minute walkthrough](https://gytung.github.io/ProseLedger/presentation.html)**. Five timed screens cover input, revision routes, an actual card-assisted edit, all six results, and exports. Press **Start 2-minute tour** once. The page embeds its data and has no model calls or external runtime assets. It displays recorded model outputs, not live generation. Manual chapter controls, pause and restart are available. The numbers come from the same `evidence.json` as the slides. See the [recording script](docs/RECORDING_GUIDE.md).

To create new writing without installing anything, open the **[browser generation demo](https://gytung.github.io/ProseLedger/create.html)**. Select a provider, enter your own model API key, and supply a topic with source excerpts. Draft mode has two model stages. Full comparison has up to fourteen: the draft and its initial review, followed by three rounds of three parallel revision routes and one blinded batch review. Inspect paragraph-level before/after edits, content checks, memory use, and all candidate and retained scores. Download the manuscripts and decision record. Bounded transport retries can add API attempts. The browser sends requests directly to the selected provider; no project server receives or stores the key. See the [browser guide](docs/BROWSER_DEMO.md) for privacy and endpoint requirements.

The browser implementation is a bounded JavaScript adaptation. Its five-dimension problem score ranges from 0 to 20 and is **not interchangeable with the frozen Python evaluation's composite score**. The original Python workflow below remains available for that protocol. Model inference takes place at the visitor's API provider, not on their computer's GPU.

Open the **[round-by-round dashboard](https://gytung.github.io/ProseLedger/#rounds)**, or download and open `docs/index.html` locally. It contains all six recorded cases, their initial and retained texts, and the decision traces. No installation, credentials or model calls are required for this viewer.

The dashboard shows the initial score (round 0), all three revision rounds, batch means and per-case curves. Candidate scores and retained-draft scores are shown separately so rejected edits remain visible. The complete [round-score CSV](docs/round_scores.csv) contains 18 initial entries and all 54 branch decision records.

The viewer inspects saved results. It does not rerun the algorithm or generate new text. The same six-case data power the project presentation.

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

## Run the application

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

The current model transport uses **OpenAI Codex CLI**. Install and authenticate it using the [official CLI instructions](https://developers.openai.com/codex/cli/). The CLI must be on `PATH`; alternatively set `PROSELEDGER_CODEX_PATH` to its executable path. Generation requires network access and an account with access to the configured model. No local model training or GPU is required.

The recorded evaluation used `gpt-6.1-sol`. The runtime retains that model contract. Fresh model outputs can differ even when the topic and sources are unchanged.

### Command-line generation

```bash
python -m proseledger run --sources data/sources.json --topic "Evidence-preserving revision of research proposals" --output runs/example
```

To resume an interrupted run, repeat the same command with `--resume`. Keep its model, topic, sources and output folder unchanged. Completed response records are reused; unfinished work may make new calls. Use a new output directory for a new experiment.

The CLI exports the initial proposal, all three retained proposals, checks, scores and per-round decisions. Runtime outputs are local and ignored by Git. They may contain supplied source text and application requests; review them before sharing.

## Design

```text
Topic + supplied sources
        |
   Ideation and adapted drafting workflow
        |
   Initial proposal + common first revision
        |
        +-- Targeted ---------------------------+
        +-- Planner-only -----------------------+--> checks --> score --> retain/reject
        +-- Memory + frozen experience cards ---+                  |
                                                                  +--> decision records
```

Memory cards carry examples, provenance and reuse conditions. A planner must bind a proposed operation to current passages. The local executor restricts changes to authorized paragraphs; an ordinary targeted fallback has a different scope. Each candidate still passes the shared checks and retention rule.

Cross-document cards stay frozen during a run. Current-branch records inform later planning but do not automatically become new cards. This is a writing-specific adaptation of verifier-aware memory governance, not a reproduction of every component or benchmark of MemGuard.

## Repository map

```text
app.py                 Local application entry point
proseledger/           Drafting, revision, checking and model transport
ui/                    Background job support
data/                  Frozen catalogue and attributed example source notes
docs/                  Static six-case viewer, evidence and documentation
tests/                 Offline checks; no paid model calls
scripts/               Publication and resource checks
```

See [architecture](docs/ARCHITECTURE.md), [reproducibility](docs/REPRODUCIBILITY.md) and [publishing instructions](docs/PUBLISHING.md).

## Development checks

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
node --test tests/browser-api.test.mjs tests/browser-engine.test.mjs tests/browser-ui.test.mjs tests/presentation.test.mjs
python scripts/check_publication.py
```

The test suite checks contracts and recorded-data consistency without generating a new proposal. Test success is not evidence of better writing quality or a successful live account configuration.

## Attribution and licensing

The drafting components adapt the MIT-licensed [LiRA implementation](https://github.com/lira-workflow/auto-review-writing). The project adds course-specific integration and revision control; it does not claim that the reused drafting graph was developed from scratch. The original notice is retained at `proseledger/drafting/LICENSE`.

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
