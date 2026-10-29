# Reproducibility

## Inspecting the recorded result

`index.html` embeds the same `evidence.json` used by the local application. It shows authentic archived texts and decisions without model calls. `summary.csv` is derived from that record. Text and source hashes identify the original artifacts.

The public release intentionally excludes raw request/response cache files and private run folders. It therefore does not offer byte-for-byte algorithm reconstruction from the old cache. A saved-results viewer is not an algorithm replay.

## Running the implemented workflow

Install the Python dependencies, configure the actual model transport, and use `python -m proseledger run` with an explicit source file, topic and new output directory. The same drafting, planning, bounded-execution, checking and retention mechanisms remain executable. Personal paths and the old presentation-cache dependency have been removed for portability.

Fresh results are new observations. The first generated idea, draft, revisions and model judgments can differ from the archived batch; the published scores are not expected outputs for every fresh run. New calls require network access, model access and account allowance. No GPU or training job is part of this workflow.

## Configuration and audit

`python -m proseledger verify` checks the bundled resources. Each new run records its model, source snapshot, topic, code/resource identities and intermediate decisions. Resuming requires the unchanged run contract and preserves committed responses. Raw local request and response records may contain source text, so they are excluded by `.gitignore` rather than distributed publicly.

Operational task templates in the Python source are part of the executable algorithm. They are included so that the method can be inspected; they are not private development-chat transcripts. Removing them would make the generation and evaluation procedures incomplete.

The release's offline tests verify data consistency, interfaces and decision contracts. They do not claim a fresh end-to-end paid model run on every supported operating system.
