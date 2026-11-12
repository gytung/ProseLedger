# Software validation

Source-package checks performed on macOS arm64 with Python 3.12.7 and Node.js 25.9.0:

| Check | Result | Scope |
|---|---:|---|
| Desktop Python contracts | 45/45 passed | Workflow, bounds, local transport, run import and loopback HTTP isolation |
| Browser JavaScript contracts | 59/59 passed | Cloud transport, checkpoints, revision protocol and detector record binding |
| Headless Chrome interactions | 10/10 passed | Generation, handoff, repair, retention, resume, cancellation, mobile layout and downloads |
| Archived research integrity | 143 source files and 15 detector inputs verified | File hashes and original result accounting |
| Controlled evaluation integrity | 24 runs, 144 writer responses and 36 detector mappings verified | Frozen model identity, inputs, seeds and text hashes |
| Published evidence manifest | 667 files verified | Includes all three public execution logs; excludes the local Ollama service log |
| Figure reproduction | 14 PDF/SVG/PNG figure sets rendered | Four plotting scripts run from a clean ZIP extraction without model calls |

All model and detector calls in the software tests use synthetic fixtures. These checks establish software behavior, not writing quality. No fresh model or detector experiment is represented by these test counts. Current Windows hardware inference has not been measured by this source-package validation. The included CI workflow runs software contracts on Windows, macOS and Linux when the repository is published.

The public browser modules are based on repository commit `069c56039a0d8c364be59d915ea0b04188f6f50c`. The source distribution includes local desktop code and the separate MLX study profile. The source-package launcher requires an installed Python interpreter; local runtime and model downloads occur only through the explicit Qwen setup action.

To repeat the checks, follow the commands in `README.md`. Browser tests use Playwright 1.62.1. A provided `PLAYWRIGHT_EXECUTABLE_PATH` may select an existing Chromium-based browser; otherwise install Playwright's Chromium build. Keep scientific model runs and software-fixture results in separate reports.

The final clean-extraction check on 13 November 2026 repeated all 45 Python and 59 JavaScript contracts, verified the public human-response counts, rendered every report figure and rechecked the 667-file evidence manifest afterward. No frozen experimental record changed during these checks. Plotting dependencies are separate from application dependencies; see `report_figures/README.md`.
