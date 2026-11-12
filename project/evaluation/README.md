# ProseLedger controlled evaluation

The directory contains a frozen, paired test of general section copy-editing versus the released six-rule revision instruction. Both conditions use the same section writer, semantic review, bounded repair and retention logic. This evaluates the naturalization instruction under a fixed verifier; it is not a test of historical memory retrieval.

- `PROTOCOL.md`: prespecified comparison, metrics and scope.
- `freeze.json`: hashes of all 12 inputs, generation scripts and engine code before inference.
- `inputs/`: complete manuscripts, controlled source packets and 72 reference facts.
- `runs/C01/generic/` and `runs/C01/rules/`: every response, original, raw candidate, retained proposal and ledger; the same layout applies to all 12 cases.
- `judgments/`: anonymous pairwise assessments in both display orders, with quotation checks and reference-fact judgments.
- `known_answer_challenges.json`: 24 constructed valid/invalid mutations tested against the deterministic guard.
- `detector/`: post-generation GPTZero responses indexed by text hash.
- `summary.json` and `case_results.csv`: the full case table and uncertainty intervals.

The 12 manuscripts are newly authored controlled fixtures of approximately 350–380 words. Their source packets explicitly identify the supplied facts and design constraints; they are not presented as real publications or naturally sampled author manuscripts. This setup makes preservation errors inspectable, but does not establish generalization to a population of research papers. The separate archived MLX study and human interview notes must not be pooled into this experiment.

## Run

Use Python 3.11 or later. Start the pinned `qwen2.5:7b-instruct-q4_K_M` model through Ollama at `127.0.0.1:11436`, with 8,192 context tokens and one parallel writer. Sign in to the official Codex CLI with access to `gpt-6.1-sol`. The runner uses the official CLI for hosted review without reading or copying account credentials. No external Python packages are required.

Start a genuinely new run from the archived package without copying previous model responses:

```sh
python reproduce.py --out ../fresh-evaluation --execute
```

The destination must not exist. The command copies only frozen inputs, engine code, scripts and protocol files, then executes all 24 writing runs, both-order anonymous judgments, known-answer checker tests and summaries. It does not overwrite archived evidence or silently reuse archived responses. Omit `--execute` to create the workspace first and inspect it before running.

Inside that new directory, the individual commands are:

On Windows PowerShell, set `$env:PYTHONUTF8="1"` before running individual scripts. The `reproduce.py --execute` wrapper sets this automatically for its child processes.

```sh
python check_challenges.py
python run_paired.py
python judge_pairs.py
python audit_challenges.py
python scan_outputs.py --key-stdin
python summarize.py
python fact_consensus.py
python cost_summary.py
python trace_summary.py
python extract_failures.py
python verify_results.py
```

Enter the GPTZero key on standard input when running the scan command. It is never saved in the experiment records. `scan_outputs.py` requires all paired generation runs to complete first. Scans are cached by exact text hash, so an unchanged final manuscript does not incur a duplicate scan.

For interrupted or failed generation, run `python run_paired.py --resume`. The request hashes bind every cached response to the unchanged input and model condition. The run record preserves prior attempts. Resume does not choose a new seed or replace an unfavourable accepted output.

## Interpretation

The primary comparison is between two conditions with the same writer model and six writer calls. Adaptive review and repair may use different numbers of hosted calls. Report those counts and token usage rather than calling the full procedure budget-matched. Model-active time is calculated from response durations; concurrent scheduler wait is not model time.

The reference-fact judgments and pairwise preferences are automated proxies, even though the branch names are hidden and both display orders are checked. They are not human ratings. A detector probability measures the detector's response to the submitted text, not the percentage of words written by a model and not preservation of meaning. All case outcomes, including unchanged text, failed calls and preferences for the generic condition, remain in the report.

The separate semantic-checker extension and its freeze record are described in `SEMANTIC_CHALLENGE_PROTOCOL.md`. It uses the same 24 fixed valid/invalid edits and receives no expected labels at model-call time. Its confusion matrices evaluate checker components on constructed mutations, not the full population of scientific manuscripts.

`report_failure_cases.md` documents a mechanism-based selection from the archived run. Fresh runs produce their own full event list through `extract_failures.py`; the curated archived report is not copied into a new workspace or presented as a result of a fresh run.
