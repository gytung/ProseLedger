# Local Qwen experiments and the archived connector

**The current public [generation](https://gytung.github.io/ProseLedger/create.html) and [revision](https://gytung.github.io/ProseLedger/revise.html) pages use cloud model APIs. They do not require Ollama, a local connector, Codex sign-in or a pairing code.** Enter your provider's API key and Model ID on those pages. See the [current workspace guide](REVISION_WORKSPACE.md).

This document preserves the context of the independent local experiment and the earlier browser-to-local connector. It is not a setup prerequisite for the public website.

## Independent local experiment package

The separately distributed desktop package runs the section writer through local Ollama and uses its configured review connection for checking and bounded repair. Follow that package's included installation and launch instructions on Windows or macOS. The package's local interface is a separate application from the public cloud pages.

The pinned Ollama writer is **`qwen2.5:7b-instruct-q4_K_M`**. Its recorded weight digest is `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`. The writing configuration uses an 8,192-token context, a 2,200-token output limit, temperature 0.2 and section seeds 42–47. Local inference requires model files, sufficient RAM and time; it does not consume purchased Qwen cloud API tokens. Review calls may still use a remote model service under the package's configured account or API access.

Installing this model does not change the model used by the current public website. Selecting cloud Qwen on the website calls the selected provider's hosted model and is a separate configuration.

## Archived browser connector

The earlier connector implementation remains available for inspection in `local_connector/`, with browser transport modules and regression tests. It paired a specific website origin with an operator's own account login on loopback port `11437`; local Qwen requests went to Ollama on port `11434` or the project-private port `11436`. A pairing code granted access to that local bridge; it was not a model API key.

The connector bundle under `docs/local/` belongs to that earlier optional integration. **Starting it or entering a pairing code is not part of the current public-page workflow.** Use the independently packaged local application for local experiments; do not follow archived connector instructions as instructions for the current cloud pages.

Where the archived integration is deliberately maintained for development, Ollama must remain bound to loopback and allow only the intended website origin. Do not expose local inference or the account connector on a public address. The current public application does not need local-network browser permission.

## Comparability and validation

The prior Mac account-plus-Ollama functional run on 13 November 2026 completed generation in 45.8 seconds and revision/checking in 282.9 seconds. It retained four changed sections, from 724 to 726 words, with the reviewer judging content preserved and readability similar. No GPTZero scan was run in that functional check. It is neither a Windows measurement nor a cloud API performance result.

The earlier frozen Mac/MLX experiment used another runtime and quantisation profile. Matching a model family or nominal parameter count does not reproduce its text or GPTZero observations. Local Ollama runs, archived MLX results and new cloud runs must retain separate inputs, model identities, outputs and validation records.

GPTZero remains an optional external observation. Each teammate may manually enter their own or a privately shared team API key where a scan is offered; no key belongs in a website, source archive or installer. Compare original and retained text only after scanning those exact texts. A detector probability is not a percentage of AI-written words, a naturalness score or proof of factual accuracy.

For the current public workflow, use [Generate and revise: workspace guide](REVISION_WORKSPACE.md). For a local reproduction, use the documentation included in the independent local package and report its own measured results.
