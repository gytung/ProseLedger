# Generate and revise: workspace guide

The public website has two workspaces. Both run in the browser through your chosen cloud model API. No software installation, Ollama, Codex sign-in or local pairing code is needed.

| Workspace | Input | Output |
|---|---|---|
| [Generate proposal](https://gytung.github.io/ProseLedger/create.html) | Topic and 2–10 source excerpts | One six-section proposal; no language revision yet |
| [Revise proposal](https://gytung.github.io/ProseLedger/revise.html) | An existing proposal and its source excerpts | Checked retained text, original/candidate comparison and revision ledger |

## Connect your API

1. Choose **OpenAI API**, **OpenRouter** or **Custom compatible API**. Enter that provider's API key and an available **Model ID**. The OpenAI preset starts with `gpt-4.1-mini`; change it if your account uses another supported model. A key from one provider does not authenticate a different provider.
2. For a custom provider, set its HTTPS base URL under **Advanced API settings**. Check the displayed destination before submitting your key. The endpoint must support the application's API format and permit browser access from this website.
3. Select **Test connection**. This makes a small real model call. Your provider account needs model access and API credit; a ChatGPT subscription or Codex login alone does not provide an API key or API credit.
4. On the revision page, leave **Section writer Model ID (optional)** blank to use the main model for writing and review in separate requests. If the same provider offers another model you want to use for writing, enter its exact Model ID. Only the six section rewrites use it; review and bounded repairs still use the main model. One provider key is used for both.

The website does not supply a shared model account. Requests travel directly from your browser to the selected provider. If a provider blocks browser requests, use a provider that supports them or run the independent local package; repeatedly submitting the same blocked request will not fix its access policy.

## Generate, then revise

1. On **Generate proposal**, supply a topic and source excerpts, confirm API usage and click **Generate proposal**. Only the supplied evidence is used; the page does not search for papers.
2. Read or download the proposal. Select **Continue to revision** to carry that exact proposal, topic and sources to the other page. Only those inputs are transferred through this tab's session storage; the transfer record is removed on arrival. No API key is transferred.
3. On **Revise proposal**, check the draft and sources. Enter your provider key again, test the connection, select a verification policy, confirm usage and click **Revise my proposal**. You can also open this page directly and paste or import your own draft.
4. Inspect **Original**, **Candidate** and **Retained**, plus section changes and reviewer findings. If the candidate fails the retention checks, the original remains clearly labelled as retained.
5. Download the manuscript, revision ledger and complete run JSON. Save a checkpoint before closing an unfinished run.

Use these six headings: **Abstract; Introduction; Related Work; Methodology; Planned Evaluation; Limitations and Conclusion**. A proposal describes planned research; this tool does not run those scientific experiments or verify reported empirical findings.

## What the revision does

Six rules address actor/action, concrete wording, redundancy, information flow, sentence focus and calibrated claims. The section writer receives the original context and evidence, and edits one section at a time. Separate review calls check meaning, attribution, uncertainty and proposal status. A flagged section can receive up to three uniquely anchored, non-overlapping repairs, covering at most 35% of its text.

The Standard policy runs section review/repair and a whole-document audit. Extended permits up to two further repair-and-audit cycles. Retention requires structural checks, no unresolved document-level findings, a model readability judgment of better or similar and final length of 85–115% of the original. These automated checks are fallible, including when writing and review use the same model.

The ledger records this run's candidates, checks and decisions. **No historical experience cards are retrieved, and no model training occurs in this workflow.** The earlier catalogue/planner experiments are a separate archived protocol.

## Credentials and recovery

The model API key stays in tab memory, is sent only to the selected provider, is excluded from checkpoints and downloads, and is cleared when a run ends. Your manuscript and source excerpts are sent to that provider as part of the model requests. Keep keys outside the recording frame and shared project archive.

Use **Stop** to cancel work. If interrupted, download the checkpoint. Open it on the same workspace, re-enter your API key and resume with unchanged input, policy and model configuration. Completed validated responses are reused. A generation checkpoint belongs on Generate proposal; a revision checkpoint belongs on Revise proposal. Earlier local-account or Ollama checkpoints cannot be resumed as cloud runs. Closing the tab stops the browser controller, but an already submitted model request may still be billed.

## Optional GPTZero observation

After revision, any teammate can manually enter their own or a privately shared team GPTZero API key. It is separate from the model API key and is never bundled in the website, code or project package.

Under **Optional external check · GPTZero**, choose **Original proposal**, enter the GPTZero key, consent to sending that text and select **Check selected text**. Repeat for **Final retained proposal**. The key is cleared after each scan, so enter it again for the second text. If the original was retained unchanged, there is one combined **Original = final retained proposal** entry. Download the detector observations to keep the result, exact-text fingerprint, timestamp and run identifier together.

GPTZero is optional: it does not select edits, trigger rewriting or alter the manuscript. Browser access and the GPTZero account allowance must permit the request. A failed scan is an error, not a zero score. Detector class probabilities are neither the percentage of AI-written words nor proof of naturalness or factual correctness.

## Keep results attached to their own runs

| Record | What it establishes | What it does not establish |
|---|---|---|
| Archived six-case Targeted/Planner/Memory evaluation | Results of that frozen three-route protocol | Performance of the current section editor |
| Earlier Mac local-Qwen/GPTZero experiments | Observations for saved texts and the recorded model/runtime configuration | The GPTZero result of a fresh cloud run |
| Prior Mac account-plus-Ollama integration check | One completed functional workflow on that configuration | Native Windows performance or current cloud API quality |
| Your current cloud run | Its own text, model IDs, checks, decisions and optional exact-text detector observations | A guaranteed naturalness improvement or fixed score decrease |

The prior local route was tested on an Apple M4 Mac with 16 GB memory on 13 November 2026. Generation took 45.8 seconds; six Qwen rewrites plus account-model review, bounded repair and a final audit took 282.9 seconds. All ten responses completed. Four sections changed, from 724 to 726 words; the reviewer judged content preserved and readability similar. No GPTZero scan was run in that functional check. These figures describe the prior Mac configuration, not the current cloud pages or a Windows test.

Synthetic tests establish software behavior. Each live cloud configuration needs its own completed run record. Cloud Qwen, local Ollama Qwen and another quantisation/runtime are not interchangeable experimental conditions.

## Record the presentation

Run and inspect your actual cloud configuration before recording. Keep the complete run JSON and show the topic/sources, real generation or revision progress, one concrete edit, its check and the downloaded output. Long waits may be shortened with an explicit time-skip label. Show GPTZero only for text that has actually been scanned. Use the numbers from that run in the accompanying slides.

The independent local experiment package has its own setup and records. It is not needed to open or run these public pages. See [local-experiment context](OLLAMA_BROWSER.md) when preparing a separate local reproduction.
