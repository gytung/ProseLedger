# Generate and revise: workspace guide

There are two public links, with separate jobs:

| Workspace | Input | Output |
|---|---|---|
| [Generate proposal](https://gytung.github.io/ProseLedger/create.html) | Topic and 2–10 source excerpts | One six-section proposal; no language revision yet |
| [Revise proposal](https://gytung.github.io/ProseLedger/revise.html) | An existing proposal and its source excerpts | Checked retained text, original/candidate comparison and revision ledger |

The browser controls the workflow. The default setup sends generation, review and repair requests through the visitor's signed-in Codex account, and runs section rewriting on that visitor's computer through Ollama. The website does not host either model or share a project account.

## Set up once

1. Download the [local connector](https://gytung.github.io/ProseLedger/local/ProseLedger_Local_Connector.zip), extract it and open **Start_Windows.bat** or **Start_Mac.command**. Choose the default full setup for Codex plus local Qwen, or the optional proposal-only setup for Codex alone. Complete Codex sign-in locally if requested. Keep the connector terminal open.
2. In the website, keep **Codex account · local connector** selected. Use the connector address, normally `http://127.0.0.1:11437`, and model `account-default`. Paste the **local pairing code** printed by the connector, then select **Test Codex connection**. This is a connection/status check, not a generation request. The pairing code is not an API key or password.
3. For **revision**, the full setup starts Ollama with `qwen2.5:7b-instruct-q4_K_M`. The first setup downloads the runtime and approximately 4.7 GB of model weights. It can reuse existing project model files rather than downloading another copy. Select the address it shows: normally project-private port `11436`; standard port `11434` is an alternative for an already configured Ollama service. Select **Test local Qwen**. The test checks the pinned installed weights; it does not download them.
4. If Chrome or Edge requests local-network access, allow it for this site. Keep the local services open. Ollama must allow the exact origin `https://gytung.github.io` and remain bound to loopback; do not expose it publicly.

Generation does not require Ollama. Revision with local Qwen requires model storage and sufficient RAM; CPU-only execution is possible but can be slow. Local Qwen does not consume purchased Qwen API tokens. Codex account access and usage limits apply.

**Optional API mode:** select OpenAI API, OpenRouter or a compatible provider, enter that provider's key and available model ID, and test it. API credit is separate from a ChatGPT subscription. In revision, either retain local Ollama or choose a hosted writer. Hosted writing uses the selected provider; it is not the recorded local-Qwen configuration.

## Generate, then revise

1. On **Generate proposal**, supply the topic and source excerpts, confirm account/API usage and click **Generate proposal**. Only supplied evidence is used; the page does not search for papers.
2. Read or download the proposal. Select **Continue to revision** to carry the exact proposal, topic and sources to the other page. Only those inputs are transferred, through this tab's session storage; the transfer record is removed on arrival. No account token, pairing code or API key is transferred.
3. On **Revise proposal**, check the supplied draft and sources. Enter the pairing code again, connect Codex and local Qwen, select a verification policy, confirm usage and click **Revise my proposal**. You can also open this page directly and paste or import your own draft.
4. Inspect **Original**, **Candidate** and **Retained**, plus the section changes and reviewer findings. A rejected candidate leaves the original clearly labelled as retained.
5. Download the manuscript, revision ledger and complete run JSON. Save a checkpoint before closing an unfinished run.

Use these six headings: **Abstract; Introduction; Related Work; Methodology; Planned Evaluation; Limitations and Conclusion**. A proposal describes planned research; this tool does not run those scientific experiments or verify reported empirical findings.

## What the revision does

Six rules address actor/action, concrete wording, redundancy, information flow, sentence focus and calibrated claims. Local Qwen receives the original context and evidence, and rewrites one section at a time. Codex separately checks meaning, attribution, uncertainty and proposal status. A flagged section can receive up to three uniquely anchored, non-overlapping repairs, covering at most 35% of its text.

The Standard policy runs section review/repair and a whole-document audit. Extended permits up to two further repair-and-audit cycles. Retention requires structural checks, no unresolved document-level findings, a model readability judgment of better or similar and final length of 85–115% of the original. Automated checks can miss errors; inspect the result.

The ledger records this run's candidates, checks and decisions. **No historical experience cards are retrieved, and no model training occurs in this workflow.** The earlier catalogue/planner experiments are a separate archived protocol.

## Credentials and recovery

The Codex pairing code is sent only to the loopback connector. API keys are sent only to their selected provider. Neither is passed to Ollama, stored in checkpoints or included in downloads; both are cleared after a run. The website never receives the Codex account login token.

Use **Stop** to cancel work. Download the checkpoint if interrupted. On the same workspace, open that checkpoint, re-enter the connection secret and resume with unchanged input, policy and model configuration. Validated completed responses are reused. A generation checkpoint belongs on Generate proposal; a revision checkpoint belongs on Revise proposal. Closing the tab stops the browser controller; an already submitted request may still consume account usage or API credit.

## Optional GPTZero observation

After revision, any teammate can manually enter their own or the team-shared GPTZero API key and scan the selected original or retained manuscript. Scanning is opt-in and sends that text to GPTZero. It does not determine retention or trigger further rewriting. Results are bound to exact text fingerprints and timestamps. Detector probabilities are neither the percentage of AI-written words nor proof of naturalness or factual correctness.

## Evidence and recording

Archived six-case scores, archived Mac Qwen results and a visitor's current run are different records. Do not attach an old score to freshly generated text. Even a matching model tag does not guarantee the same weights/runtime as an earlier profile, the same draft, reviewer, sampling outcome or GPTZero version.

Earlier release checks included synthetic-provider browser tests and a nine-response native-adapter run with `gpt-6.1-sol`: 713 original words, 722 retained words and six changed sections, across two attempts after a review timeout. That was an engine check through a native test adapter, **not** an end-to-end measurement of the current Codex-plus-Ollama web route. No GPTZero observation was made for that check. Synthetic tests verify software behavior, not writing quality; current run quality must be assessed from its own saved outputs.

The current local-account/local-writer route was also tested on an Apple M4 Mac with 16 GB memory on 13 November 2026. One fresh generation took 45.8 seconds; six Qwen rewrites plus Codex review, a bounded repair and final audit took 282.9 seconds. All ten model responses completed without failed calls. The retained candidate changed four sections (724 to 726 words); the reviewer judged content preserved and readability similar. This is a functional run, not evidence of improved naturalness or a GPTZero decrease. No detector scan was run. Chrome also made real, unmocked connection probes to both local services. Windows launch scripts and automated tests are included, but this Mac test is not a native Windows measurement.

For a presentation recording, complete and inspect your actual run first, keep its full record, and show its inputs, real generation/revision progress, one concrete edit, its check and the downloaded output. Long waits may be shortened with an explicit time-skip label. Show GPTZero only when that exact text has been scanned. Keep pairing codes and API keys out of the recording.
