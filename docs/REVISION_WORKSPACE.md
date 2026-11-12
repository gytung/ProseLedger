# Proposal-to-manuscript workspace

Open **https://gytung.github.io/ProseLedger/create.html**. This workspace runs the revision controller in the visitor's browser. Model calls go directly to the visitor's chosen HTTPS API provider. It does not host a model or execute the desktop package's local Qwen installation.

## User journey

1. Enter a provider API key and model ID, then test the connection. In the advanced endpoint settings, an optional section-writer Model ID can use another model offered by that same provider; generation, review and repair use the main model. A ChatGPT subscription or Codex sign-in is not an API key for this static page.
2. Supply a topic and two to ten source excerpts, or paste an existing six-section research proposal with those sources. Source notes are the evidence available to the writer; this page does not search for papers.
3. Start the workflow. It generates an initial proposal when needed, rewrites six sections, independently reviews the candidates, repairs specific issues within bounded spans, and reviews the assembled manuscript.
4. Inspect the retained manuscript, the original and candidate, and each section's checks and changes. An unsuccessful candidate leaves the original available and clearly identified.
5. Download the retained manuscript and the revision ledger. Save a checkpoint before closing the tab if the run is unfinished.

The six required section headings are Abstract, Introduction, Related Work, Methodology, Planned Evaluation, and Limitations and Conclusion. The tool produces a research proposal; it does not execute the proposed scientific experiments.

## What is checked

Six editorial rules address actor and action, concrete wording, redundancy, information flow, sentence focus and calibrated claims. They guide expression while preserving substantive claims and supplied evidence. Separate review calls inspect meaning, attribution, uncertainty and planned-versus-completed status.

Bounded repairs permit up to three non-overlapping, uniquely anchored replacements per section, covering no more than 35% of that section's existing text. Final retention also requires structural checks, no unresolved full-document findings, a non-worse model readability judgment, and a final length between 85% and 115% of the original. These checks can miss errors; inspect the final manuscript before use.

The Standard policy runs section repair and a full-document audit. The Extended policy allows up to two additional bounded repair-and-audit cycles. Extra calls use additional API credit. The ledger records this run only. No historical experience-card retrieval or model training occurs in this workflow.

## Credentials, interruption and recovery

The API key remains in the current tab's memory and is cleared after execution. It is not written to browser storage or downloaded run records. Choose only an API provider you trust: that provider receives the key, topic, source notes and manuscript. Browser requests require provider CORS support; this workspace does not route keys through a shared proxy.

Completed responses can be saved in a checkpoint. Resume requires the same input, policy and model configuration; successful responses are reused rather than billed again. A checkpoint is a user-saved record, not an independently signed scientific result. Closing the tab stops the browser controller; an already submitted provider request may still incur a charge.

## Optional GPTZero observation

After generation, a separate GPTZero API key can check a selected manuscript. Scanning is opt-in, sends that text directly to GPTZero, and does not influence retention. The result is bound to the exact text fingerprint. Class probabilities are detector observations, not the proportion of words written by AI or proof of natural writing. No archived Mac result is substituted for a visitor's new run.

## Validation

The browser integration suite uses synthetic provider responses to test rendering, bounded repair, original restoration, interruption recovery, secret-free exports and narrow-screen behavior. These fixtures test software behavior, not model quality. Actual model outcomes vary with provider, model and input; hosted browser outcomes must not be represented as measurements from the separate frozen local-Qwen Mac experiment.

### Release checks

- 139 Node contract and regression checks passed, including 13 section-revision engine checks.
- Five real-Chrome interaction tests passed with synthetic provider fixtures: generation and bounded repair, interruption and checkpoint resume, final rejection restoring the original, invalid input without an API call, and cancellation. The suite also checks secret-free exports, literal rendering of untrusted text and a 390-pixel layout.
- One fresh end-to-end model run used the same JavaScript engine with the signed-in native account adapter and `gpt-6.1-sol`. It completed nine model responses across two attempts; one section-audit attempt exceeded the native adapter deadline. Resume reused seven validated responses. The initial proposal contained 713 words; the retained revision contained 722, with six changed sections. The automated reviewer reported content preserved and readability better. These are model judgments, not blinded human ratings.
- This real-model check validates the engine with a native test adapter, not a new end-to-end public API-provider certification. Public browser transport behavior is covered by the HTTP fixture suite; each visitor should test their actual endpoint and model before running. The public page itself cannot use subscription account login.
- No GPTZero scan was made for this release check, and no archived detector score is assigned to it.
