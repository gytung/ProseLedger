# Architecture

The application has two independent uses: generating a new proposal and inspecting an existing six-case evaluation. Viewing recorded results never starts a new model call.

## Generation

`proseledger/runner.py` owns the run contract and orchestration. `pipeline.py` provides shared requests, scoring and candidate selection. `draft_workflow.py` calls the graph in `drafting/builder.py`; the graph is an adapted drafting backbone rather than a new graph algorithm.

1. Read attributed source notes and the research topic.
2. Generate ideas and select the first idea according to the fixed protocol.
3. Generate the six-section initial proposal through the drafting graph.
4. Evaluate the initial proposal and execute a Targeted first revision.
5. Compare Targeted continuation with Planner-only and Memory continuations.
6. Check each retained result against the initial draft and export all branches.

## Revision control

`targeted.py` implements feedback-guided whole-proposal revision. `revision_controller.py` implements the two planning routes. Planner-only has an empty historical catalogue; Memory receives the frozen catalogue. Both retain their own prior-round records.

`memory_planning.py` presents the available cards to the planner and validates current-text bindings. The five-card catalogue is small enough to inspect in full; this is not embedding-based top-k retrieval. A planner can decline every card. At most three editing actions are authorized in one plan, not three successes plus three failures.

The controller chooses exactly one route before writing:

- `local_edit`: execute a validated plan within authorized paragraphs;
- `targeted_fallback`: use an ordinary Targeted rewrite grounded in current feedback;
- `stop`: retain the current proposal without a new edit.

A failed local attempt does not trigger an extra writer sample. `local_executor.py` enforces the local edit contract. Text outside authorized windows is preserved in that route; the whole-proposal fallback has a different scope.

## Checking and retention

`preservation.py` combines structural/citation constraints with a model content audit. `pipeline.evaluate_version` computes the shared score: 0.3 times rule severity plus 0.7 times model rubric severity. These weights are not calibrated to human preferences.

A candidate replaces the current proposal only when the content check passes and its score is no worse. Consequently, the retained-score curve cannot increase; its shape alone is not evidence that memory works. Checkers can miss errors or raise false concerns.

## Two memory timescales

The catalogue is frozen across the run. It stores development-derived operations, examples, provenance and reuse conditions. It is not a trained model or an automatically growing store.

The local history records actions, check outcomes, candidate and retained scores, and adoption decisions. In the present protocol, planning starts at round two with an empty branch history. Round three can read its own round-two outcome, not the other branch's outcomes. New records do not automatically update the frozen cards.

## Data and transport

`data/` contains the frozen resources required by new generation. `docs/evidence.json` contains the public, recorded six-case outputs used by the viewer. Private execution caches are created under the selected local run directory and are excluded from Git.

The model adapter uses a locally installed, authenticated Codex CLI. It requests model text and logs the execution evidence locally. Access and model availability are external prerequisites; the source package does not contain an account or entitlement.
