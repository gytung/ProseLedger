# Architecture

ProseLedger contains a current browser writing application and a preserved Python research prototype. They have different orchestration and retention contracts. The recorded six-case dashboard belongs to the Python protocol; it is not an evaluation of the new browser rules.

| Property | Current browser protocol 3 | Archived Python protocol |
|---|---|---|
| Entry | `docs/create.html` | `app.py` / `python -m proseledger run` |
| Initial text | Generated proposal or supplied six-section draft | Generated through the adapted drafting graph |
| Revision start | Three independent routes from D0 | All routes share the first Targeted revision |
| Editing instructions | Six conditional editorial rules, with exact edit-level traces | Earlier feedback and conditional planning contracts |
| Revision scope | One to three paragraph replacements, or stop | Local edit, whole-proposal Targeted fallback, or stop |
| Retention | Content checks pass and blind paired preference is better | Content checks pass and composite score is non-worsening |
| Score | Five expression dimensions, total 0–20 | 30% rule severity + 70% model severity |
| Transport | Visitor's browser calls their selected provider | Local authenticated model CLI |
| Evidence | Fresh browser runs and separately labelled saved walkthrough | Frozen six-case results in `docs/evidence.json` |

## Current browser application

[Open the live editor](https://gytung.github.io/ProseLedger/create.html?v=20261030f) or the [saved language-edit walkthrough](https://gytung.github.io/ProseLedger/writing-demo.html?v=20261030f). The latter makes no model calls.

### Control flow

`docs/assets/browser-engine.js` exposes `runProposal`. A transport function is injected; the engine does not receive or store API credentials.

1. Validate the topic, two to ten source notes, and frozen cards. If a draft is supplied, check its length, six-section structure, and citation identifiers before model calls.
2. Either generate three ideas, select the first, outline and draft in one request; or use the supplied text directly. The result records `draftOrigin` and does not fabricate idea-generation records for a supplied draft.
3. Audit D0 for expression problems anchored to exact passages and for content support. The audit is independent of the route and is the same under standard and explicit-rule editor configurations.
4. Start Targeted, Planner-only and Memory independently from this same D0. There is no shared first revision.
5. In each of up to three rounds, obtain bounded candidate edits or a stop from each active route. Planner-only and Memory return explicit plans; Memory can also apply conditional historical cards.
6. Validate the edit and its rule evidence, apply replacements, and review changed candidates using anonymous IDs. The reviewer does not receive branch names, historical cards, writer plans, rule-attribution labels or previous numeric scores.
7. Retain only a changed candidate that passes the structural/content checks and is preferred over its own preceding draft. Keep ties and rejected candidates in the record; use the preceding draft for the next round.
8. Export the initial proposal, retained manuscripts, all candidates, scores, rule traces, memory applications and decisions.

A generated comparison has at most fourteen logical calls. A supplied-draft comparison has at most thirteen. Draft-only generation has two calls, whereas review-only supplied-draft mode has one. The transport allows at most two simultaneous HTTP requests; a third route queues. Retries can add HTTP attempts. These are call ceilings, not identical token budgets or a dollar spending cap.

### Operational language rules

`docs/assets/naturalness-rules.js` defines six rules: actor/action specificity, concrete wording, redundancy removal, information flow, sentence focus, and calibrated claims. Each includes a goal, applicability condition, exception, positive example and invalid counterexample. The examples are illustrative specifications, not human-rated outcomes or facts for the new manuscript.

`runProposal({ruleMode: 'explicit'})` supplies this catalogue to every editor. A changed paragraph must include one to three records containing `ruleId`, `paragraphId`, `beforeQuote`, `afterQuote`, and `reason`. `validateRuleApplications` checks the rule ID, exact quote membership, actual changed paragraph and bounded record count. Each resulting `row.edits[]` contains its own `rules[]`, and the row also exposes `ruleApplications`.

These checks make an edit traceable. They do not prove that the selected rule is the best semantic explanation or that it caused an improvement. Quality and content judgments are assessed separately. No rule calls for banning all hyphens, shortening every sentence, deleting uncertainty or avoiding technical terms.

`ruleMode: 'standard'` supplies a general natural-academic-prose editing instruction without the explicit catalogue or rule-attribution claims. The initial audit and blind-review instructions remain unchanged. This option supports a future same-D0 comparison; implementing it is not evidence that the explicit rules outperform the control. The public form defaults to explicit mode.

### Editing, memory and retention

Targeted can edit paragraphs named by the current anchored diagnosis. Planner-only and Memory can inspect the whole text for a concrete editing opportunity, then return a plan with protected phrases and its bounded replacement paragraphs. All routes receive their own recent decision history; only Memory receives historical cards. No route receives another route's decisions.

`applyLocalEdits` applies at most three paragraph replacements covering at most 4,500 original characters. Paragraph IDs are stable within a candidate call and recomputed from the next retained draft. Text outside authorized paragraphs remains unchanged. The browser has no whole-proposal Targeted fallback.

A memory application must name a supplied card, bind it to an actual changed paragraph, and quote current-text evidence for applicability. A card present in the prompt is not automatically counted as used. Successful mechanical binding is not proof of effective transfer. A retained uncarded Memory edit cannot be credited to a later rejected card-guided edit.

The catalogue remains frozen. Branch-local records preserve attempted edits, rule explanations, checks, preferences and adoption outcomes; they inform subsequent decisions but do not automatically become new reusable cards. There is no model training, cross-visitor learning or uncontrolled public memory growth.

Structural checks cover the six headings, supplied citation IDs, source-ID preservation, numeric token changes and apparent completed-study claims. The model content audit separately examines meaning, qualifications and evidence relationships. Both are fallible. Acceptance also requires the anonymous paired review to prefer the candidate. All absolute scores are recorded unchanged; a preferred candidate can have a higher absolute rating because these are distinct model judgments. The UI exposes disagreement rather than forcing a monotonic curve.

### Browser components and checkpoints

| File | Responsibility |
|---|---|
| `docs/assets/browser-engine.js` | Input contract, drafting/audit orchestration, routes, bounded edits and retention |
| `docs/assets/naturalness-rules.js` | Shared conditional editorial specifications |
| `docs/assets/create-app.js` | Input state, exact-request caching, edit evidence, score views and exports |
| `docs/assets/api-client.js` | Provider destination, authentication in memory, streaming, deadlines and bounded retries |
| `docs/assets/run-checkpoint.js` | Credential-free portable workspace and contract-aware restoration |
| `docs/assets/external-validation.js` | Opt-in GPTZero observations outside the editor |

GitHub Pages serves static code and public inputs; it does not relay model calls or store visitor keys. Model requests go directly to the visitor's selected provider. Checkpoints preserve exact inputs, successful response records and attempt history, but no credentials. A supported protocol-2 record is view-only and cannot resume under protocol-3 editor instructions. A record with legacy attempt history is also read-only. Imported files are user records, not authenticated research evidence.

### External detector observations

The GPTZero connector sends a selected manuscript directly to the fixed official endpoint only after the visitor supplies a separate GPTZero API key and consents. It records human/mixed/AI class probabilities, available confidence information, a timestamp, and the exact text's SHA-256 fingerprint. These estimates are not naturalness scores or percentages of AI-written sentences.

Detector observations never enter the writer, score, paired review, retention decision or memory admission. Four authenticated browser scans completed for the main recorded run: the initial draft and all three retained outputs were classified as AI with probability 1.0 and high confidence. The detector did not distinguish the four texts. The recorded viewer validates manuscript hashes before attaching these observations. The live panel refreshes after generation or imports and labels observations from previous runs or earlier text versions; it never transfers an old observation to a new manuscript. Blinded human assessment remains a separate evaluation rather than a feature this connector replaces.

## Archived Python application and six-case protocol

The following describes the preserved Python implementation only. Its source attribution, model contract, scores and recorded data remain intact.

### Generation

`proseledger/runner.py` owns the run contract and orchestration. `pipeline.py` provides shared requests, scoring and candidate selection. `draft_workflow.py` calls the graph in `drafting/builder.py`; the graph is an adapted drafting backbone rather than a new graph algorithm.

1. Read attributed source notes and the research topic.
2. Generate ideas and select the first idea according to the fixed protocol.
3. Generate the six-section initial proposal through the drafting graph.
4. Evaluate the initial proposal and execute a Targeted first revision.
5. Compare Targeted continuation with Planner-only and Memory continuations.
6. Check each retained result against the initial draft and export all branches.

### Revision control

`targeted.py` implements feedback-guided whole-proposal revision. `revision_controller.py` implements the two planning routes. Planner-only has an empty historical catalogue; Memory receives the frozen catalogue. Both retain their own prior-round records.

`memory_planning.py` presents the available cards to the planner and validates current-text bindings. The five-card catalogue is small enough to inspect in full; this is not embedding-based top-k retrieval. A planner can decline every card. At most three editing actions are authorized in one plan, not three successes plus three failures.

The controller chooses exactly one route before writing:

- `local_edit`: execute a validated plan within authorized paragraphs;
- `targeted_fallback`: use an ordinary Targeted rewrite grounded in current feedback;
- `stop`: retain the current proposal without a new edit.

A failed local attempt does not trigger an extra writer sample. `local_executor.py` enforces the local edit contract. Text outside authorized windows is preserved in that route; the whole-proposal fallback has a different scope.

### Checking and retention

`preservation.py` combines structural/citation constraints with a model content audit. `pipeline.evaluate_version` computes the shared score: 0.3 times rule severity plus 0.7 times model rubric severity. These weights are not calibrated to human preferences.

A candidate replaces the current proposal only when the content check passes and its score is no worse. Consequently, the retained-score curve cannot increase; its shape alone is not evidence that memory works. Checkers can miss errors or raise false concerns.

### Two memory timescales

The catalogue is frozen across the run. It stores development-derived operations, examples, provenance and reuse conditions. It is not a trained model or an automatically growing store.

The local history records actions, check outcomes, candidate and retained scores, and adoption decisions. In the present protocol, planning starts at round two with an empty branch history. Round three can read its own round-two outcome, not the other branch's outcomes. New records do not automatically update the frozen cards.

### Data and transport

`data/` contains the frozen resources required by new generation. `docs/evidence.json` contains the public, recorded six-case outputs used by the viewer. Private execution caches are created under the selected local run directory and are excluded from Git.

The model adapter uses a locally installed, authenticated Codex CLI. It requests model text and logs the execution evidence locally. Access and model availability are external prerequisites; the source package does not contain an account or entitlement.
