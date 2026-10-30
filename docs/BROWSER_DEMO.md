# Browser generation demo

Open [ProseLedger — Generate a proposal](https://gytung.github.io/ProseLedger/create.html). No installation, local Python environment, or GPU is required. The workflow runs in your browser and sends model requests directly to the provider you select. The model itself runs on the provider's infrastructure, not on your computer.

For a presentation or screen recording, use the [two-minute recorded walkthrough](https://gytung.github.io/ProseLedger/presentation.html). It shows the genuine six-case evaluation used in the slides, requires no API key, and makes no model requests. Fresh generation is a separate workflow and is not expected to reproduce the recorded scores.

This page generates a research **proposal** from supplied evidence. It does not conduct experiments, establish research findings, or reproduce the separate archived Python evaluation.

## Start a run

1. **OpenAI is selected by default**, with API base `https://api.openai.com/v1` and model `gpt-4.1-mini`. Confirm that the model is available to your API project. OpenRouter and a custom OpenAI-compatible Chat Completions endpoint are also supported.
2. Enter **your own** OpenAI Platform API key, or the key for the provider you select. API billing is separate from ChatGPT Plus or Codex subscription access. This page has no Sign in with ChatGPT integration: a subscription login is not an API key. Your provider bills your API account for requests. See [OpenAI's ChatGPT and API billing guide](https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform).
3. Enter a research topic. Use the supplied source excerpts for a first attempt, or provide your own supported source input. Check that the evidence actually supports your topic. The demo uses the supplied text; it does not browse or read the full papers behind links.
4. Choose a mode. **Draft** has two model stages: ideas, outline and a six-section proposal in one response, followed by an initial review. **Compare** continues through three revision rounds. Each round runs three independent editors concurrently and then reviews the candidates together, for at most fourteen model stages in total. A route that finds no useful safe edit stops early; later round slots explicitly record that no new request was made. Transport retries can add API attempts. Each route has the same number of editing opportunities; the Memory context is longer, so token budgets are not identical.
5. Review the destination and data notice, confirm that the selected provider may receive your input, then start generation. Keep the tab open until the run finishes.
6. Inspect the proposal, source references, checks, and scores. Download the Markdown proposal, JSON record, or CSV scores you want to retain.

There is no universal completion time: network latency, provider queues, and model speed vary. The page reports streaming activity, elapsed time, and provider usage. Transport attempts have bounded timeouts. Transient failures are retried at most once within the overall request deadline; authentication errors are not retried. A stalled request no longer waits indefinitely. Completed model responses remain in this tab so a stopped run can resume without regenerating successful stages. Enter the key again and keep the original provider, model, topic, and sources for a continuation.

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

Compare mode starts all three routes independently from the same initial proposal. It does not copy a common first revision into every branch. Each round distinguishes:

| Route | Revision procedure |
| --- | --- |
| Targeted | Propose paragraph edits directly from current review feedback. |
| Planner-only | State an explicit bounded editing plan, then supply the paragraph edits, without historical cards. |
| Memory | Use the same planning procedure with compact conditional editing cards and branch-local success/failure feedback. |

Each editor returns bounded replacements by stable paragraph IDs. The application applies those replacements deterministically; untouched paragraphs remain unchanged. Planner and Memory expose their editing rationale. Memory must identify the applicable card and explain why its conditions fit the current passage; a card is not credited merely because it was included in the prompt. No useful edit is also a legitimate outcome. Invalid edits are recorded rather than silently inserted into the proposal.

Memory cards describe operations, applicability conditions, things to preserve, counterexamples, and historical examples. Their provenance and verification limits remain in the supplied catalogue. Historical acceptance is not proof that a card improves a new proposal. The demo does not train a model, update the public catalogue, or learn across visitors.

## Read the scores correctly

The browser audit rates five problem dimensions: clarity, specificity, flow, concision, and academic style. Each ranges from 0 to 4; the total is a **0–20 problem score, where lower is better**. Fractional values allow finer distinctions, but do not make the judgment objectively precise. The review supplies issues anchored in actual passages; a nonzero total requires at least one such issue. The dimensions are model judgments, not calibrated measurements.

The initial review also locates specific issues. Later reviews compare each candidate against its own previous draft. The batch review receives anonymized pairs without route names, card IDs, or advertised method benefits. The same preservation criteria and editing budget apply across routes. Position and judge-model biases remain possible.

Retention uses a separate decision: structural/content checks must pass, and the paired reviewer must judge the candidate meaningfully better. Ties keep the previous draft, avoiding changes without an identified benefit. Absolute scores remain visible exactly as returned by the reviewer. A retained candidate can therefore have a slightly higher absolute score even when the paired review prefers it. The interface exposes that disagreement instead of smoothing it away. Neither a better pairwise judgment nor a lower score is proof of a general advantage.

The main evidence is now **the edit itself**. Inspect the before/after paragraphs, how much text changed, the attempted and accepted edits, preservation findings, and the actual Memory card applications. Candidate scores and retained scores are shown separately. If all final drafts really are identical, the interface says so. A flat curve may reflect a good initial draft, no applicable edit, rejected edits, or an insensitive reviewer; it must not be presented as a successful revision by itself.

Automated checks are fallible. They can miss unsupported claims or reject a valid edit. Passing them is not a human quality judgment or proof of factual correctness. The same selected model writes and audits the text, which is another limitation.

The separate [saved evaluation dashboard](https://gytung.github.io/ProseLedger/#rounds) reports earlier frozen Python runs. Those archived scores combine rule and model components with 30%/70% weights. This browser's 0–20 audit uses a different protocol. Do not compare the numbers directly or present a new browser run as a reproduction of the archived six cases.

## Data and key handling

- The API key is used in the current page session. The application does not save it in browser storage, its repository, or a project backend, and clears its working key after the run finishes or stops. The key is excluded from the application's exported run records.
- Model requests go directly from your browser to the selected API endpoint. They include your topic, supplied source excerpts, generated text, and the feedback or editing examples needed for each stage. The selected provider receives the key for authentication and applies its own data and billing policies.
- GitHub Pages serves the static application and public example data. It is not a relay for model requests. There is no shared project API key and no inference server operated by this demo.
- A password field masks the key on screen; it does not make browser-held credentials inaccessible to malicious extensions or compromised page code. Only use a device, browser, site, and endpoint you trust. Do not paste private material into a provider you have not authorized to receive it.
- A custom endpoint must use HTTPS and allow cross-origin browser requests. Confirm the displayed destination before sending your key. Never use a public CORS proxy to work around a provider restriction.
- Model and source text are displayed as text rather than executed as page code. Downloaded records can contain your topic, excerpts, and generated text, so check them before sharing.

Refreshing or closing the page loses the current in-memory run and continuation cache. Download outputs before leaving. If you cancel, completed records can be downloaded as a partial run; incomplete stages are not replaced with sample results. Resume reuses successful responses from this same tab when the exact request matches. Missing or invalidated requests are retried, and dependent stages are recomputed when their inputs change. Starting a new run discards that continuation cache. Cancellation stops further browser requests but may not stop an already processing provider request or reverse its charge.

For provider guidance, see [OpenRouter authentication and key limits](https://openrouter.ai/docs/api_reference/authentication) and [OpenAI API key safety](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety). OpenAI recommends keeping long-lived keys out of browser applications in production; this visitor-supplied demo does not provide server-side secret isolation.

## Validation record

See the [30 October engineering validation](BROWSER_VALIDATION.md) for two full real-model runs, their unmodified outputs, the test scope, and the limits of that evidence.

## Troubleshooting

| Message or symptom | What to do |
| --- | --- |
| Authentication failed / HTTP 401 | Check that the key belongs to the selected provider and has not expired or been revoked. |
| Insufficient credits / HTTP 402 | Add provider credits or use an account/model with available credit. |
| Access denied / HTTP 403 | Check account restrictions and permission to use the model. |
| Model or endpoint not found / HTTP 404 | Copy the model ID from your provider. Check the API base URL and Chat Completions compatibility. |
| Rate or usage limit / HTTP 429 | One bounded retry may be attempted. Review account limits if it still fails; the demo never switches providers automatically. |
| Browser cannot reach the provider | Check connectivity and whether the endpoint permits browser CORS requests. Command-line access alone does not establish browser support. Try a supported preset; do not disable browser security. |
| Timed out | A request exceeded a first-response, idle, or overall deadline. Save partial records, then resume in the same tab after checking connectivity. A completely new run may produce different text. |
| Invalid JSON, missing fields, or an invalid edit | The model did not follow the response or editing contract. Invalid candidates are recorded; valid branches can still be reviewed. If a required draft or review stage fails, save the partial record and resume or try a model with stronger structured-output instruction following. |
| Output truncated | Use a model with adequate output capacity. The demo rejects truncated text rather than treating it as a complete proposal. |
| Scores differ from a previous attempt | Generation and model evaluation can vary, including with the same inputs. Record the actual model, inputs, protocol, and results for the run being discussed. |
| Memory does not beat Targeted | This is a valid outcome. Review whether the cards fit the current issue, whether planned changes were applied, and why candidates were retained or rejected. Do not omit losing cases. |

Only use your own API credentials. Do not put keys in screenshots, support messages, issues, commits, or shared exports.
