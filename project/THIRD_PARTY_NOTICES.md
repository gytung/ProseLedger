# Third-party notices

The project retains the MIT copyright and permission notices in `LICENSE`. The current source distribution contains the section-revision application and browser workspaces, together with the separate MLX research profile. It does not include the earlier drafting-graph implementation, model weights, account sessions or runtime binaries.

The verification ledger adapts a governance principle from **MemGuard: Persisting Verifier Signals for LLM-Agent Memory Governance**, https://arxiv.org/abs/2608.21867. The production application is not a distribution of MemGuard and does not implement its full memory-retrieval pipeline.

The optional contrastive research decoder is an independent CoPA-inspired implementation, https://aclanthology.org/2025.emnlp-main.433/. The reported selected writer uses lambda=0. The research profile retains its source manifest and separate method documentation.

Local setup downloads Ollama and `qwen2.5:7b-instruct-q4_K_M`. The MLX profile separately uses `mlx-community/Qwen2.5-7B-Instruct-4bit`. These model distributions derive from Qwen2.5-7B-Instruct; their own model licenses apply. Ollama is MIT-licensed. Download URLs and integrity fingerprints are recorded in `platform/local_runtime_sources.json`. Optional official Codex CLI access uses the operator's own installation and account.

Source-paper excerpts retain attribution, source URLs and available license metadata in `examples/` and research inputs. The project code license does not relicense these texts. Python, Node.js, MLX, Playwright and model-service dependencies retain their respective licenses. No provider credentials are included in this distribution.
