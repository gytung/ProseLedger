# Local Qwen in the browser workspace

The [revision page](https://gytung.github.io/ProseLedger/revise.html) uses **Ollama on your own computer** for section rewriting. Its default reviewer connection uses the local account connector and your existing signed-in Codex account for initial drafting, checking and bounded repair. No Qwen API key or separate OpenAI API key is needed for this default arrangement. The page itself cannot launch local programs or sign into the account: start the local services first.

## Prepare the local writer

1. Install Ollama, or use the local runtime prepared by the desktop project package.
2. Ensure the model `qwen2.5:7b-instruct-q4_K_M` is installed. The workspace checks the model digest before using it; it does not silently substitute another model or switch to a cloud writer.
3. Start Ollama on a loopback address. A normal Ollama installation uses `http://127.0.0.1:11434`; the project's private runtime uses port `11436`.
4. Permit only this website's origin by setting `OLLAMA_ORIGINS=https://gytung.github.io` before starting Ollama. Restart an already-running Ollama process for the setting to take effect. Do not set the origin to `*` or expose Ollama on a LAN address.
5. Open the website in Chrome or Edge. If the browser asks for local-network access, allow it for this site. Do not disable browser security. If organisational policy blocks local access, use the local desktop application instead.

The connector package linked from both pages prepares the website-origin setting and starts the local services. Its setup downloads the pinned Qwen model when it is missing. The project's private Ollama port, `11436`, is selected by default; `11434` remains available for an existing standard Ollama installation. Neither route creates a public inference server.

## Run the writing workflow

Use [Create proposal](https://gytung.github.io/ProseLedger/create.html) to generate the initial proposal only; it does not call Ollama. Its **Continue to revision** action transfers the draft and sources to [Revise proposal](https://gytung.github.io/ProseLedger/revise.html). Alternatively, open the revision page and paste an existing proposal and its source notes.

On the revision page, select **Local Qwen2.5 7B · Ollama** as the section writer and choose the port used by your local process. Click the local connection test first. A successful check confirms the exact installed model; it does not download it.

For the main connection, keep **Codex account · local connector** selected, start the account connector, and enter the pairing code it displays. This pairing code is not an OpenAI API key. The connector binds to loopback port `11437` and uses the officially signed-in account locally. The pairing code is sent only to that connector, never to Ollama or a cloud API endpoint. Test the required connections, supply the topic and source excerpts on the creation page or the existing proposal on the revision page, confirm usage, and start the run. The handoff transfers only proposal input, never credentials; re-enter the connector pairing code on the revision page.

Alternatively, a hosted-API connection requires a provider-issued API key with credit. A ChatGPT subscription is not an API key. Hosted API mode remains optional and has separate billing; it is not the default account-based route.

Only the six section-rewriting requests go to Ollama. Generation, independent review and bounded repair go through the selected main connection: the signed-in account connector by default, or the explicitly selected hosted API. The reviewed final draft and revision ledger remain downloadable. Closing the page or stopping a request preserves completed responses in a checkpoint; resume requires the same reviewer connection, model and local writer identity.

The text supplied to the local writer includes the manuscript and source excerpts. Those materials also reach the account's model service, or the selected API provider, during generation and review. Local rewriting does not make the whole workflow offline or private from that service.

## Interpret the results correctly

This route uses the desktop package's Ollama model tag and writer parameters, but a new model run can still produce different text. The original frozen Mac/MLX experiment used a separate runtime and quantisation profile. Neither a local Ollama run nor a cloud-Qwen run automatically reproduces that experiment's GPTZero numbers.

## Optional GPTZero comparison

Team members may use the GPTZero API key shared privately by the project owner. Each person enters it manually in the masked field; it is not included in the website, source code or connector package. This is a separate credential from the Codex pairing code and any model API key.

After a revision completes, open **Optional external check · GPTZero** below the results. Under **Proposal to check**, choose **Original proposal**, paste the GPTZero key, tick the consent box and click **Check selected text**. Then choose **Final retained proposal** and repeat. The key is cleared after each scan, so enter it again for the second text. If the original was retained unchanged, the selector shows one combined **Original = final retained proposal** entry; there are not two different texts to compare. Click **Download detector observations** to save the observations, text fingerprints and run identifier.

The current webpage sends each selected manuscript directly to `https://api.gptzero.me/v2/predict/text`; it does not route GPTZero through the local connector or a proxy. Browser access, service access and the shared account's allowance must permit the request. If it fails, keep the error and the completed manuscript; no detector result is inferred.

GPTZero remains an optional observation. Its result does not change the manuscript or determine which revision is retained. Displayed percentages are detector class probabilities, not a measured percentage of words written by AI, and should be reported alongside human judgments and content checks.

Reference: [Ollama server and origin configuration](https://docs.ollama.com/faq), [Chrome local-network access](https://developer.chrome.com/blog/local-network-access).
