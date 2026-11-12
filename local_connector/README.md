# Archived ProseLedger local connector

**This connector is not required or used by the current public website.** [Generate proposal](https://gytung.github.io/ProseLedger/create.html) and [Revise proposal](https://gytung.github.io/ProseLedger/revise.html) now run directly through each visitor's cloud model API key and Model ID. No installation, Ollama, Codex sign-in or pairing code is needed for those pages.

The connector is retained for the earlier optional browser-to-local integration and source inspection. The instructions below apply only to a preserved, matching earlier browser build. They do not describe the current public pages. For a current local reproduction, use the separately distributed desktop package and its own instructions.

This earlier launcher connects a compatible browser build to **your own computer and account**. It does not depend on another group member's Mac or contain account credentials or model weights.

## Earlier integration: start

1. Extract the **whole ZIP** into a writable folder. On Windows, use **Extract all** first; do not launch from inside the ZIP. A short path such as `C:\ProseLedgerConnector` is convenient.
2. Double-click **Start_Windows.bat** on Windows, or **Start_Mac.command** on macOS. If macOS blocks the downloaded launcher, use Finder's Open action and the normal Privacy & Security approval for this file. Do not disable system protections.
3. Press Enter for the full workflow. The launcher reuses installed tools where possible, downloads missing official runtimes, and prepares the pinned **Qwen2.5 7B Instruct Q4_K_M** model. The first model download is about **4.7 GB**; Windows runtime files can add about 2 GB. Allow **15 GB free disk space** and preferably **16 GB RAM**. CPU-only generation can take several minutes per section.
4. If asked, sign in to **your own Codex account** in the official login flow. This mode uses that account's access and limits; an OpenAI API key is not required. A subscription does not provide unlimited calls.
5. Keep the launcher window open. Copy its **pair code** into the website's **Local pairing code** field. The code changes each time the connector restarts. It is not an API key or account password.

## Earlier integration: matching browser pages

Use a preserved browser build that still has **Codex account · local connector**, **Local pairing code** and **Test local Qwen** controls. The current public `create.html` and `revise.html` do not have these controls and do not call this connector.

On the first page, leave **Codex account · local connector** selected, paste the pair code, and click **Test connection**. Supply a topic and source excerpts, then generate. Download the proposal, or click **Continue to revision** to transfer the same draft and sources into the second page.

On the revision page, paste the pair code again, test the account connection, and select **127.0.0.1:11436 · project private service** for Ollama. Click **Test local Qwen**. Allow this website to access your local computer if Chrome or Edge asks. Import your proposal and its source excerpts if you did not use the handoff button, then start revision. Qwen rewrites sections; Codex checks and repairs meaning changes. Download the retained manuscript and run record when finished. A failed check can retain original wording; it does not promise a score reduction.

**GPTZero is optional and separate.** Any teammate can manually enter their own or the team-shared GPTZero API key to scan the final output. No key is bundled or prefilled. Generation, revision and downloads also work without a GPTZero key.

## Reuse an existing desktop installation

Extract this connector folder **inside or next to** the desktop `ProseLedger` folder to reuse its `runtime/models` and runtimes. An ordinary Ollama installation's `~/.ollama/models` is also checked. Advanced users can set `PROSELEDGER_PROJECT` to the desktop project folder, or `OLLAMA_MODELS` to their existing model directory before launching. No personal paths are built into this package.

## Recovery

- **Download interrupted:** restart the launcher; model downloads resume.
- **Port 11436 is occupied:** close the earlier project's local-model launcher first, then restart. This launcher does not kill another application's service or change its origin settings.
- **Port 11437 is occupied:** close the older connector window before opening a second one.
- **Browser cannot connect:** keep the launcher open, use the displayed pair code, and allow local-network access for `gytung.github.io`. Use a current Chrome or Edge browser. Browser/device policies may prevent public pages from reaching loopback; the desktop package remains an alternative.
- **Account limit or model unavailable:** check the official account login and allowance. Leave the account model as `account-default` unless you have a specific available model ID.
- **A request fails:** the page keeps completed stages; use Resume after fixing the connection. Export the run/checkpoint before closing the tab.

The connector binds only to `127.0.0.1`, accepts the exact public website origin, and requires its session pair code. It never copies the official account's authentication files. Runtime downloads have fixed SHA-256 checks. No personal API keys belong in this folder or a public repository.

Automatic setup targets **64-bit Intel/AMD Windows 10 22H2 or Windows 11**, and **macOS 14+**. Native Windows operation requires validation on the team's Windows computer; the same launchers and network/security contracts are covered by automated tests where supported. Model/runtime differences can change outputs; this connection is not a numerical replay of the earlier Mac MLX experiment.
