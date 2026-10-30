# Two-minute recording walkthrough

Open https://gytung.github.io/ProseLedger/presentation.html and press **Start 2-minute tour**. The five screens advance at 0:00, 0:20, 0:40, 1:16 and 1:44, ending at 2:00. Use a maximized browser window, preferably 1280 x 720 or larger. Rehearse once before recording. The page pauses if its tab becomes hidden. Chapters and arrow buttons support manual control; Restart returns to the first screen.

This is an inspection of recorded model outputs that match the project slides. It performs no model calls, stores no keys and loads no external runtime assets. Once loaded, the walkthrough does not require an API or a network connection. Source data, text and results are embedded. Downloads contain the selected manuscript, Case 02 decision evidence, and score trajectories for all six manuscripts. Full evidence for every manuscript remains in the main dashboard.

For fresh generation, use the separate Generate new link and your own OpenAI API key. API billing is separate from ChatGPT subscriptions. This public page does not integrate ChatGPT subscription sign-in; a Plus account is not a value to enter in the API key field. Local Codex clients support ChatGPT sign-in, but that is a different access path. See [OpenAI billing](https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform).

## Spoken script

**[0:00 · INPUT]**

This is ProseLedger, our research-writing system. We are viewing the recorded run behind our slides. Here, three attributed source notes support a research topic on citation integrity. The system turns that input into a six-section proposal.

**[PAUSE — NEXT SCREEN — ROUTES]**

We compare three revision routes. Targeted uses specific feedback. Planner adds a bounded editing plan. Memory adds conditional experience cards inspired by MemGuard. All routes share the first revision; later candidates face content checks before they can replace the current draft.

**[PAUSE — NEXT SCREEN — MEMORY]**

Here is an actual memory edit. The planner selected a card for replacing broad payoff language with a comparison already in the text. The highlighted change removes a vague closing phrase while preserving the planned evaluation and workload measures. The edit passed its checks and was retained at seven, with no score improvement. In round three, the planner stopped rather than inventing missing methodological details. This separates using experience from benefiting from it.

**[PAUSE — NEXT SCREEN — RESULTS]**

Across all six manuscripts, the mean automated problem score falls from 8.40 initially to 6.88 for Targeted, 7.00 for Planner, and 7.12 for Memory. Lower is better. Memory ties Targeted four times and loses twice. Retention rules explain why kept-score curves cannot rise. These complete results establish an operational workflow, but no average memory advantage.

**[PAUSE — NEXT SCREEN — OUTPUT]**

We can download the actual drafts and decision records. Our next step is better experience matching, followed by blinded human review. Every displayed result remains traceable to its source record.

## Interpretation

The displayed six-case results use the archived 30% rule / 70% model composite, not the fresh browser expression score. Targeted supplies the common first revision in this archived protocol. Planning adds calls, so total token costs are not equal. Scores are automated, not reconciled human judgments. Memory finishes with zero wins, four ties and two losses against Targeted. The adopted Case 02 card edit has no score improvement; its next decision stops. Do not describe this record as evidence of a memory advantage or as live generation.

Rebuild this page with `python scripts/build_presentation_demo.py`; the source is `docs/evidence.json`. Run `node --test tests/presentation.test.mjs` to validate the data and recording controls.
