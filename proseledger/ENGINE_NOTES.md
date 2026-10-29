# Runtime map

The publication package contains one generation runtime. Its proposal-drafting
subsystem derives from LiRA and retains the upstream MIT license in
`drafting/LICENSE`; the repository's attribution files describe that reuse.
`SOURCE_PROVENANCE.json` records the extraction lineage. These source identifiers
are not dependencies on old folders.

## Generation

1. `runner.execute` validates explicit sources and loads `data/catalogs.json`.
2. `pipeline.create_ideas` proposes three ideas; the first is selected without
   selecting by eventual score.
3. `draft_workflow.generate_draft` runs the source-analysis, outline, writing,
   review, and editing graph in `drafting/builder.py`.
4. `targeted.run_targeted` provides the targeted comparison. Its first completed
   revision is shared with the two planning branches.
5. `revision_controller.run_candidate_branch` executes Planner-only and Memory.
   `memory_planning` checks card applicability and binds exact current passages;
   `local_executor` applies only authorized paragraph replacements. The controller
   can select a local edit, targeted fallback, or stop. It does not resample a
   failed local edit for an extra writing opportunity.
6. `preservation.check_content_preservation` and the common selection rule check
   each candidate. `runner` saves every route's retained proposal and summary.

The Memory branch adds a frozen catalog of development-derived cards to the same
planning process. Planner-only has no historical cards. Both planning branches
retain their own earlier public outcomes within a run; neither writes those
outcomes back into the frozen catalog. No model training occurs.

The score is 30% transparent style rules and 70% a fixed model rubric. Lower is
better. It is not an authorship probability, and passing automated checks does
not establish factual correctness. Planning adds calls, so total token budgets
are not equal. All branches and all outcomes must be reported.

## Storage and publication

`data/` includes only explicit sample sources, a topic, the compiled catalog, and
a resource checksum manifest. The card construction and trace verification took
place during development; the published runtime consumes the compiled catalog.
It does not require private trace directories or rebuild that catalog online.

A new run creates a local request-response cache and a complete decision trail
under its chosen output directory. That cache is required for exact interrupted
run recovery. It is not part of the source distribution. Keep runs outside
tracked source, and review outputs before publishing them. The repository's
`.gitignore` excludes default run directories and model-call caches.

`docs/index.html` and the dashboard's Saved evaluation page read archived results.
They do not call a model or regenerate archived responses. The source release
intentionally does not ship raw request-response transcripts or expose the old
saved-response reconstruction command.

Some internal protocol identifiers retain historical schema names because these
names participate in persisted record formats. They do not load earlier code
versions. Fresh model runs can differ in ideas, text, and scores from archived
results even when the topic and sources are the same.

## Checks

`python -m proseledger verify` checks resource hashes and imports the graph. It
makes no model calls. `python -m pytest` exercises synthetic local-edit, route,
checkpoint, and publication-boundary cases. Synthetic fixtures are not research
results. These tests do not replace a live hosted-model run or physical Windows
validation.
