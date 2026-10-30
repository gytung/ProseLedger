# Browser workflow validation — 30 October 2026

This page preserves earlier protocol-2 checks. For the current protocol-3 editorial rules, recorded comparisons and limitations, see [Natural-writing validation](NATURALNESS_VALIDATION.md). The older results below are not evidence for the new rule contract.

This is an engineering smoke test of the rewritten browser workflow, not a quality benchmark or evidence that Memory outperforms another route.

## Latest usability release: 20261030d

The live page now starts with a two-call draft, can continue comparison from that same cached draft, supports portable credential-free checkpoints, and separates card application from retained card-guided edits. HTTP concurrency is capped at two; provider cooldowns and reasoning-stream activity are handled explicitly. Score-axis zoom changes only the view.

A new full workflow check completed with **12 fresh model calls in 7 minutes 43 seconds**, with no failed calls or invalid stages. Targeted stopped because the initial reviewer found no actionable expression issue. Planner retained one local clarification; Memory retained no changes. All retained numeric scores remained 0. This illustrates why the interface exposes text changes and decisions, not only a score curve. Memory used a card in one rejected candidate; no retained edit is credited to it.

The run used the unchanged browser engine through an authenticated local model adapter (`gpt-6.1-sol`). It does not validate a visitor’s browser API credentials, provider CORS settings, or a fixed completion time. Transport, interruption, resumption, credential routing, checkpoint validation and UI transitions were covered by 88 passing JavaScript tests; all 84 existing Python tests also passed. Browser import, round navigation and downloads were also inspected using actual model output.

[Latest live-workflow outputs and all 12 model responses](validation/ux-live-check.zip). No archived score was substituted into this run. Earlier checks below remain historical engineering evidence, not a pooled benchmark.

## Earlier test scope

- Two newly generated inputs were run through the exact browser engine with real `gpt-6.1-sol` calls through a local authenticated model adapter. No stage used a saved response in these two runs.
- This verifies model generation, structured responses, the three-route workflow, content checks, retention and exported records. It is not a claim that authenticated browser requests to every supported API provider were tested.
- Browser transport, failure recovery and UI behavior were covered by 50 automated JavaScript tests. Existing Python validation remained unchanged and its 84 tests passed.
- Browser rendering was inspected separately using the real responses as a clearly labelled local UI fixture. That rendering check does not make additional model calls.
- Both final-version test runs are reported below. Earlier development/debug runs informed fixes and are not included as final-version validation.

## Full final-version results

Problem scores are 0–20, lower is better. Retention requires passing preservation checks and a paired judgment of **better**. Tied candidates do not replace the previous draft. Absolute ratings are not adjusted to agree with the paired decision.

| Run | Fresh model calls | Elapsed | Initial | Targeted | Planner-only | Memory |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| shipped-default | 12 | 6:21 | 0 | 0 | 0 | 0 |
| shipped-citation | 14 | 6:41 | 0.5 | 0 | 0.5 | 1 |

Elapsed times include the local model adapter and concurrent validation workloads; they are not a promised duration for visitor API accounts. Token usage in the raw adapter records also includes its runtime overhead and is not an estimate of direct browser API billing.

| Run | Route | Retained changed rounds | Better / tied / worse judgments | Card-bearing attempts |
| --- | --- | ---: | --- | ---: |
| shipped-default | targeted | 0 | 0 / 0 / 0 | 0 |
| shipped-default | planner | 1 | 1 / 2 / 0 | 0 |
| shipped-default | memory | 0 | 0 / 2 / 0 | 1 |
| shipped-citation | targeted | 2 | 2 / 0 / 0 | 0 |
| shipped-citation | planner | 3 | 3 / 0 / 0 | 0 |
| shipped-citation | memory | 1 | 1 / 2 / 0 | 1 |

The paired counts cover changed candidates against their own previous draft, including rejected candidates; they are not wins against another route. A card-bearing attempt is not proof of a useful or retained memory contribution.

Low or flat absolute scores still occur, especially when the initial draft has no diagnosed expression defects. The revised interface exposes actual word changes, paired review evidence, unchanged drafts, rejected candidates and applicable cards rather than implying that every curve must fall. These small tests do not establish a general quality gain, and Memory is not guaranteed to win.

## Inspect the records

- [Default-topic run and all model responses (ZIP)](validation/shipped-default.zip)
- [Citation-support run and all model responses (ZIP)](validation/shipped-citation.zip)

Each archive contains the corresponding JSON record, compressed without changing any fields or responses.

The original archived six-case Python evaluation is unchanged and uses a different rubric. Its scores must not be pooled with these runs.

## Engine identity

`docs/assets/browser-engine.js` SHA-256:

`4fd5be7f2909b09218fe9cea4e1d7c41fc0e66953ce8b6c6033ffb35d524e560`

## Repeat the automated checks

```sh
node --test tests/browser-api.test.mjs tests/browser-engine.test.mjs tests/browser-ui.test.mjs tests/browser-checkpoint.test.mjs tests/presentation.test.mjs
python -m pytest -q
python -m proseledger verify
python scripts/export_round_scores.py --check
python scripts/check_publication.py
```

To make a new model run, open `create.html`, enter your own provider API key and model ID, load the example and choose Full comparison. New responses and scores may differ. The source record, model, decisions and raw outputs can be downloaded from the page.
