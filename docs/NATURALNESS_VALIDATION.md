# Natural-writing workflow: execution checks and limits

Release: `20261030e`; browser protocol: `proseledger-browser-3`.

The change makes editorial decisions explicit and inspectable. It does **not** establish that explicit rules or Memory improve writing quality on average. Every completed comparison is reported below, including the standard-instruction control.

## What changed

Six conditional editing rules cover specific subjects and actions, concrete wording, redundancy, information flow, sentence focus and calibrated claims. Each rule has an applicability condition, a prohibition, a teaching example and a bad alternative. The examples are instructional; they are not experimental results.

For each actual changed paragraph, the writer must identify a valid rule and exact before/after quote anchors. The engine checks those anchors, bounded edit scope, section structure and citations. A separate paired model review checks preservation and whether the candidate is better than the retained draft. A valid rule explanation alone is insufficient for acceptance. Tied candidates retain the previous draft. These automated checks are fallible and do not replace a human assessment.

Targeted uses current feedback. Planner-only adds a bounded plan. Memory uses the same planner with conditional historical cards. The browser branches share the initial draft but make independent first-round revisions. They do not share the first Targeted revision as the older Python protocol did. At most three paragraphs may be edited per opportunity. There are three opportunities, including explicit stop/no-edit outcomes.

Absolute problem severity remains 0–20 (lower is better), using clarity, specificity, flow, concision and academic style. No score weight was changed to favor a branch. Scores can remain flat or disagree with a paired preference. The old six-case Python evaluation used a different composite rubric and must not be pooled with these records.

## Real model checks

The actual browser engine was executed through an authenticated local model adapter with `gpt-6.1-sol`. These are real model responses, not hand-written fixtures. This tests model generation and the engine; it does not verify an authenticated browser request with every provider or a visitor's credentials. The UI was inspected separately with the resulting credential-free checkpoints.

| Comparison | Initial | Targeted | Planner-only | Memory | Fresh calls | Reused stages | Elapsed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Fresh draft, explicit rules | 1.5 | 0 | 1 | 0 | 12 | 2 | 231 s |
| Same draft, standard instructions | 1.5 | 0 | 0 | 0 | 11 | 2 | 182 s |
| Existing handoff draft, explicit rules | 1 | 0.5 | 0 | 1 | 13 | 0 | 235 s |

These are **three comparisons on two initial manuscripts**, not three independent manuscripts. The first two comparisons reused the exact same initial draft and initial diagnosis. Only writer instructions change between explicit and standard mode; diagnosis and review instructions are held fixed. Later feedback and branch decisions naturally differ. This single exploratory pair supports no score advantage for explicit rules: Planner-only was worse under the explicit contract. Independent blinded readers and repeated runs are still needed.

The reused generation and diagnosis originally took approximately 70 seconds. Thus the main explicit demonstration represents about five minutes of model work including those stages, not a two-minute live generation. Its 231-second comparison duration excludes the reused stages. Timings are observations, not guarantees for visitors. The two-minute walkthrough displays saved real outputs and performs no new model calls.

All three comparisons completed without transport or invalid-response failures. A candidate rejected by the preservation check is an editorial outcome, not a failed network request. The handoff prose was reused without deliberately adding defects; only two headings were renamed to match the browser format.

## Memory attribution

In the main explicit run, the retained Memory round-3 edit made the referent explicit:

> Before: Each entry will record the original wording, its role
>
> After: For each claim, the ledger will record its original wording, its role

This is an actual excerpt under `information_flow`, not a constructed demonstration. **It used no historical card.** Its acceptance must not be credited to memory reuse.

In the handoff run, Memory did use `caveat_consolidation` in later editing attempts, but those card-bearing attempts were not retained. Its retained edit used no card. The interface distinguishes retrieval, execution and retention instead of treating retrieval as success. No retained historical-card benefit was established in these checks.

## Development record

A preceding development run, `natural-fresh`, generated the shared initial draft and diagnosis. Its initial/final scores were 1.5 and 0/0/0; it used 14 fresh calls and took 231 seconds. Two teaching-example wordings were refined afterward. It is preserved in the raw archive as development evidence and is not silently substituted for the final-code explicit run. Across this development run and all three comparisons there were 50 fresh calls. Cached stages are explicitly labelled in the records.

## GPTZero and human evaluation

The optional connector sends only the selected manuscript, after explicit consent, directly to GPTZero using the visitor's separate GPTZero API key. It records the returned classification, confidence, timestamp and a hash of the scanned text. It neither changes scores nor controls generation, retention or memory admission. A lower detector score is not evidence of better prose.

The connector passed mocked success/error/cancellation tests. The unauthenticated browser preflight to the official endpoint returned HTTP 204 with the required origin and headers allowed. **No authenticated GPTZero scan was run; no detector results are claimed.** Its API key and billing are separate from the generation provider. See [official API reference](https://docs.gptzero.me/api-reference/) and [quickstart](https://docs.gptzero.me/quickstart/).

The next quality study should randomize text order and hide branch labels. Readers should separately rate clarity, natural flow, appropriate academic tone and meaning preservation, then state a pairwise preference. Preserve ties and all outcomes. Compare explicit versus standard instructions on the same initial drafts, and Memory versus Planner-only to isolate historical examples. Detector observations should be reported separately. Earlier informal interviews do not count as this new controlled human evaluation.

## Inspect and reproduce

- [Recorded walkthrough](writing-demo.html?v=20261030e): the same records used by the presentation.
- [Evidence JSON](natural-writing-evidence.json): full decisions, manuscripts, six rules, run metadata and source hashes.
- [Raw execution archive](validation/natural-writing-checks.zip): all four inputs/results, model messages and responses, including reused-stage labels. Adapter usage includes runtime overhead and is not a browser API billing estimate.
- [Live generator](create.html?v=20261030e): enter an API key and a model available to that API account. A ChatGPT subscription alone is not a browser API credential.

To isolate revision behavior, choose the existing-proposal mode and paste the exact initial text. Retain the same sources, model and settings. Live generations can differ even with identical inputs; use saved records for exact numerical inspection. Imported legacy protocol-2 runs are read-only and cannot resume under protocol 3.

```sh
node --test tests/*.test.mjs
python -m pytest -q
python scripts/build_writing_demo.py
python scripts/check_publication.py
```

No model call or secret is required to inspect the recorded walkthrough or run the offline checks.

Release checks: 118 JavaScript tests passed, covering transport, engine behavior, rule anchors, checkpoints, live UI, the optional detector connector and the timed walkthrough. The existing 84 Python tests passed. The publication audit confirmed that the complete older six-case batch and its 54 decisions remain unchanged. Browser inspection covered actual retained/rejected edits and a 390-pixel viewport.
