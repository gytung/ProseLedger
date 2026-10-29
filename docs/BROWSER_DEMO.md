# Browser generation demo

Open [ProseLedger — Generate a proposal](https://gytung.github.io/ProseLedger/create.html). No installation, local Python environment, or GPU is required. The workflow runs in your browser and sends model requests directly to the provider you select. The model itself runs on the provider's infrastructure, not on your computer.

This page generates a research **proposal** from supplied evidence. It does not conduct experiments, establish research findings, or reproduce the separate archived Python evaluation.

## Start a run

1. Choose a provider. OpenRouter is the suggested starting point; OpenAI and a custom OpenAI-compatible Chat Completions endpoint are also supported.
2. Enter **your own** API key and a model ID available to your account. A ChatGPT or Codex subscription is not an API key. Your provider bills your account for requests.
3. Enter a research topic. Use the supplied source excerpts for a first attempt, or provide your own supported source input. Check that the evidence actually supports your topic. The demo uses the supplied text; it does not browse or read the full papers behind links.
4. Choose a mode. **Draft** makes three model calls: ideas and outline, a six-section draft, and an initial audit. **Compare** continues through the three revision routes and uses at most 21 calls in total. Planning adds calls, so the routes do not have identical token budgets.
5. Review the destination and data notice, confirm that the selected provider may receive your input, then start generation. Keep the tab open until the run finishes.
6. Inspect the proposal, source references, checks, and scores. Download the Markdown proposal, JSON record, or CSV scores you want to retain.

Start with Draft mode if you are checking a new key, model, or endpoint. There is no universal completion time: network latency, provider queues, and model speed vary. Compare mode makes more calls than Draft mode. A model call has a three-minute timeout; failed calls are not automatically retried.

Use a separate, limited-budget key for the demo. The call count and output limits bound the workflow, but they are not a dollar-denominated spending cap. Set a spending limit at the provider if needed.

## What the workflow produces

The draft contains six sections:

1. Abstract
2. Introduction
3. Related Work
4. Methodology
5. Planned Evaluation
6. Limitations and Conclusion

The system proposes three ideas and selects the first under the demo protocol, without choosing an idea by its final score. Citations refer to the source IDs supplied to the run. Experiments remain planned, and claims should remain limited to the available evidence.

Compare mode starts all routes from the same initial proposal and shares the first Targeted revision. Subsequent rounds distinguish:

| Route | Revision procedure |
| --- | --- |
| Targeted | Rewrite using specific feedback from the current audit. |
| Planner-only | Plan a bounded edit without historical editing cards. |
| Memory | Use the same planning procedure with five frozen conditional editing cards and branch-local decision history. |

The planner may request a local edit, fall back to a Targeted rewrite, or stop. Local changes must match complete original paragraphs; text outside the authorized window remains unchanged. An invalid plan does not earn an extra writer attempt.

Memory cards describe operations, applicability conditions, things to preserve, counterexamples, and historical examples. Their provenance and verification limits remain in the supplied catalogue. Historical acceptance is not proof that a card improves a new proposal. The demo does not train a model, update the public catalogue, or learn across visitors.

## Read the scores correctly

The browser audit rates five problem dimensions: clarity, specificity, flow, concision, and academic style. Each receives an integer from 0 to 4; their total is a **0–20 problem score, where lower is better**. Positive problem scores require a quotation from the candidate text.

A candidate is retained only when the deterministic checks and model preservation audit pass and its problem score does not increase. Otherwise, the previous draft remains selected. A rejected candidate may therefore have a different score from the draft retained at that round. A stop decision produces no new candidate.

The chart shows the initial draft at round 0 and the three revision rounds. A retained-score curve that stays flat or decreases is a consequence of the selection rule. It is not, by itself, evidence that memory helps. Compare the routes' final drafts, scores, checks, and actual use of cards. Memory can win, tie, or lose.

Automated checks are fallible. They can miss unsupported claims or reject a valid edit. Passing them is not a human quality judgment or proof of factual correctness. The same selected model writes and audits the text, which is another limitation.

The separate [saved evaluation dashboard](https://gytung.github.io/ProseLedger/#rounds) reports earlier frozen Python runs. Those archived scores combine rule and model components with 30%/70% weights. This browser's 0–20 audit uses a different protocol. Do not compare the numbers directly or present a new browser run as a reproduction of the archived six cases.

## Data and key handling

- The API key is used in the current page session. The application does not save it in browser storage, its repository, or a project backend, and clears its working key after the run finishes or stops. The key is excluded from the application's exported run records.
- Model requests go directly from your browser to the selected API endpoint. They include your topic, supplied source excerpts, generated text, and the feedback or editing examples needed for each stage. The selected provider receives the key for authentication and applies its own data and billing policies.
- GitHub Pages serves the static application and public example data. It is not a relay for model requests. There is no shared project API key and no inference server operated by this demo.
- A password field masks the key on screen; it does not make browser-held credentials inaccessible to malicious extensions or compromised page code. Only use a device, browser, site, and endpoint you trust. Do not paste private material into a provider you have not authorized to receive it.
- A custom endpoint must use HTTPS and allow cross-origin browser requests. Confirm the displayed destination before sending your key. Never use a public CORS proxy to work around a provider restriction.
- Model and source text are displayed as text rather than executed as page code. Downloaded records can contain your topic, excerpts, and generated text, so check them before sharing.

Refreshing or closing the page loses the current in-memory run. Download outputs before leaving. If you cancel, completed records can be downloaded as a partial run; incomplete stages are not replaced with sample results. Cancellation stops further browser requests but may not stop an already processing provider request or reverse its charge.

For provider guidance, see [OpenRouter authentication and key limits](https://openrouter.ai/docs/api_reference/authentication) and [OpenAI API key safety](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety). OpenAI recommends keeping long-lived keys out of browser applications in production; this visitor-supplied demo does not provide server-side secret isolation.

## Troubleshooting

| Message or symptom | What to do |
| --- | --- |
| Authentication failed / HTTP 401 | Check that the key belongs to the selected provider and has not expired or been revoked. |
| Insufficient credits / HTTP 402 | Add provider credits or use an account/model with available credit. |
| Access denied / HTTP 403 | Check account restrictions and permission to use the model. |
| Model or endpoint not found / HTTP 404 | Copy the model ID from your provider. Check the API base URL and Chat Completions compatibility. |
| Rate or usage limit / HTTP 429 | Wait or review your account limits. The demo does not silently retry or switch providers. |
| Browser cannot reach the provider | Check connectivity and whether the endpoint permits browser CORS requests. Command-line access alone does not establish browser support. Try a supported preset; do not disable browser security. |
| Timed out | The individual call exceeded three minutes. Save completed records and try again later or choose a faster supported model. A new run may produce different text. |
| Invalid JSON, missing fields, or an invalid plan | The model did not follow the required response structure or editing contract. The run stops instead of inventing a replacement result. Save the partial record and try a model with stronger structured-output instruction following. |
| Output truncated | Use a model with adequate output capacity. The demo rejects truncated text rather than treating it as a complete proposal. |
| Scores differ from a previous attempt | Generation and model evaluation can vary, including with the same inputs. Record the actual model, inputs, protocol, and results for the run being discussed. |
| Memory does not beat Targeted | This is a valid outcome. Review whether the cards fit the current issue, whether planned changes were applied, and why candidates were retained or rejected. Do not omit losing cases. |

Only use your own API credentials. Do not put keys in screenshots, support messages, issues, commits, or shared exports.
