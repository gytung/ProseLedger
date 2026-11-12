# Qwen MLX research profile

This is the Apple Silicon research path used for the reported Qwen/GPTZero study. It is independent of the application’s hosted-model route. It rewrites a supplied six-section proposal locally, verifies the candidate through a hosted review service, applies bounded repairs and saves an inspectable record. It does not train a model or retrieve historical memory cards.

## What is included

- `run_revision.py`: fresh execution of the selected section-rewrite policy.
- `contrastive_transfer.py`: local Qwen writer; the runner selects `qwen_plain`, **lambda = 0**, with section seeds 42–47. The optional lambda = 0.5 decoding variant remains in the implementation for research transparency; it was not the successful selected policy.
- `audit_contrastive.mjs`, `repair_sections.mjs`, `repair_final_audit.mjs`: independent section review, exact bounded repair and the separately evaluated full-audit extension.
- `guard.mjs`, `bounded_patches.mjs`: deterministic checks and patch admission.
- `targeted_engine.mjs`, `run_targeted.mjs`: optional hosted Targeted control, starting from the same explicitly supplied manuscript.
- `archive/`: frozen inputs, source excerpts, model outputs, checks, final decisions, detector responses, original summaries and original freeze records. The two cohorts remain separate.
- `SOURCE_MANIFEST.json`: source and packaged SHA-256 fingerprints, including every portability change. Historical freeze hashes remain unchanged.

The archive contains scientific model requests inside experiment records where needed to inspect the method. It contains no account credentials, private conversation logs, downloaded weights or old project archive. Response caches and development alternatives unrelated to the reported Qwen policy are excluded; the full development summary preserves their reported outcomes.

## Requirements

Use an **Apple Silicon Mac**, Python 3.12, Node.js 20 or later, and sufficient memory and disk space for the approximately 4 GB model download and inference working set. MLX is not the Windows runtime. This directory does not install or emulate a Windows Qwen service.

The writer runs locally and needs **no Qwen API key**. Independent review and repair use the official Codex CLI, an authenticated account and its available model quota. They require network access. The optional GPTZero measurement uses the operator’s own GPTZero API key and quota. A ChatGPT subscription does not provide a general OpenAI API key.

The recorded model is `mlx-community/Qwen2.5-7B-Instruct-4bit`, pinned to revision `c26a38f6a37d0a51b4e9a1eb3026530fa35d9fed`. `requirements-revision.txt` preserves the recorded core dependency pins. It is not a complete transitive dependency lock. Model-service or library changes can alter fresh outputs.

## Install and run

From the source package root:

```sh
python3.12 -m venv .qwen-env
source .qwen-env/bin/activate
python -m pip install -r research/qwen_mlx/requirements-revision.txt
npm install -g @openai/codex
codex login
python research/qwen_mlx/prepare_contrastive_model.py
python research/qwen_mlx/run_revision.py \
  --input research/qwen_mlx/archive/heldout/case03/dev_initial.md \
  --sources research/qwen_mlx/archive/heldout/case03/dev_input.json \
  --out runs/qwen-case03-new \
  --policy section
```

The preparation command downloads weights separately through Hugging Face and writes a local model-path file. It does not package weights or run generation. The CLI must be on `PATH`; alternatively set `PROSELEDGER_CODEX_PATH` to the installed executable. A new output directory is mandatory, so recorded results are not overwritten. Run `--help` before starting if needed.

Use the exact headings, in order: `Abstract`, `Introduction`, `Related Work`, `Methodology`, `Planned Evaluation`, `Limitations and Conclusion`. Sources may be a JSON list or a JSON object with a `sources` field. `proposal.md` is the retained text; `run.json` contains the final decision; `revision_ledger.json` records this run’s edits and verification. Stage logs and candidate/audit files support diagnosis if a service call fails. On a stage failure the original manuscript is retained and the command reports failure.

The supplied reviewer transport defaults to the recorded `gpt-6.1-sol` model. Access depends on the authenticated account. The transport retains its original text-only request contract and provenance; it does not inspect or copy authentication files.

## Policies and paired runs

`--policy section` reproduces the procedure evaluated on the first four fresh manuscripts. Each section is rewritten, audited and, where possible, repaired by at most three exact, non-overlapping patches covering no more than 35% of its candidate text. The assembled manuscript must pass deterministic and independent model checks, preserve length within 85–115%, and receive a readability judgment other than “worse”. Otherwise the original is retained.

`--policy full-audit` adds at most two further bounded repair rounds for full-document findings. It was evaluated on two additional manuscripts. Its outcomes are not pooled with the first frozen policy.

To rerun a cohort on the frozen inputs:

```sh
python research/qwen_mlx/run_cohort.py \
  --cohort heldout --out runs/qwen-heldout-new --with-targeted
```

Choose `confirmation` for the separate two-case extension. `--with-targeted` makes additional hosted calls for a fresh paired control. Without it, only the Qwen path is run; the archived baseline remains available for inspection but is not a contemporaneous control. The Targeted control and Qwen path have different writers and computation budgets. This is not a matched-budget ablation. Cohort re-runs do not regenerate or select initial drafts. No detector probability is used to choose an edit or retain a candidate.

## Optional GPTZero validation

Run only after candidate selection:

```sh
python research/qwen_mlx/detector_console.py --input-root runs
```

At the hidden prompt, enter your own GPTZero API key. Then enter a JSON line, using the actual run path:

```json
{"path":"runs/qwen-case03-new/proposal.md","label":"qwen-case03-new"}
```

An empty line ends the session. The saved response includes the submitted-text hash and returned detector version. Measure the matching original or Targeted control separately. The client makes no automatic detector-guided revision. Its default session budget is 24 successful scans.

## Inspect the recorded evidence without model calls

```sh
python research/qwen_mlx/verify_archive.py
node research/qwen_mlx/test_bounded_patches.mjs
```

These commands verify file fingerprints, detector inputs, cohort means and six bounded-patch checks. They do not generate new texts, spend quota, or establish new model performance. `VALIDATION.json` records packaging checks separately from the archived scientific results.

The first four fresh cases have a mean GPTZero AI-class probability of **90.86% versus 100%**, with **1 lower / 3 unchanged / 0 higher**. The best fresh result is **63.42%**. A seen development example reached **62.61%** and is excluded from that mean. The later two-case policy had **no decrease**. All fresh cases remained AI-classified. These probabilities are not the percentage of AI-authored words, writing quality, or human naturalness ratings. No new blinded human evaluation was collected. The baseline saturates at 100%, so zero increases cannot establish general non-inferiority. The common source packet, small samples, different writers and unmatched budgets limit causal attribution. Historical memory retrieval is absent; the results do not isolate a MemGuard benefit. New generation and detector updates need not reproduce the exact archived numbers.

## Attribution

The profile is extracted from the project’s research extension; source fingerprints identify the precise origin of each included component. The text-only review adapter retains the original request wrapper for protocol continuity. The Targeted control retains the project’s browser policy and six editorial rules. This research profile does not vendor the older drafting graph.

The optional contrastive decoder is an independent adaptation of CoPA: https://aclanthology.org/2025.emnlp-main.433/. Its tested contrastive candidate failed the content gate; the selected lambda=0 path must not be called a successful CoPA reproduction. Qwen model weights are downloaded separately and retain their model license. Included source-paper excerpts retain author, source URL, excerpt and license metadata in the archived input JSON. The MIT code license does not replace those content licenses. The full repository’s third-party notices remain applicable to components included elsewhere.
