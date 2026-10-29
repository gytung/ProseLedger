# Third-party notices

## Adapted drafting components

`proseledger/drafting/` contains components adapted from LiRA, including graph construction, researchers, writers, review/edit agents, utilities and task templates.

- Source repository recorded for the adaptation: https://github.com/lira-workflow/auto-review-writing
- Recorded commit: `2bc77a6e7b30586343119bd104cc07ebaec380a1`
- Paper: https://arxiv.org/abs/2510.05138
- License: MIT
- Original copyright: `Copyright (c) 2025 lira-workflow`
- Full original notice: `proseledger/drafting/LICENSE`

Changes integrate explicit local sources, a six-section proposal contract, the project model transport and revision controls. Reused components retain their original attribution. Internal state names and protocol identifiers may retain upstream or historical names for compatibility.

## MemGuard

The revision-memory design draws on *MemGuard: Persisting Verifier Signals for LLM-Agent Memory Governance* by Haoyu Wang, Guangyuan Dong, He Liang, Zijing Zhang, Jiachen Luo, Chao Xue, Chuang Liu and Hao Tang.

- Paper URL recorded in the supplied bibliography: https://arxiv.org/abs/2608.21867
- Repository URL printed in the supplied paper: https://github.com/whyyyyy123/MemGuard

This repository contains a writing-specific adaptation of the design principle; it does not vendor the MemGuard implementation or claim its published benchmark results. Publication status is not used as evidence of this project's effectiveness.

## Source-paper excerpts

Example source notes retain their titles, author lists, source URLs, quotation/excerpt status and license metadata in `data/sources.json`. The included ACL Anthology materials are identified there as CC BY 4.0. Embedded source notes in `docs/evidence.json` and `docs/index.html` retain their recorded attribution. The MIT code license does not replace the licenses of those materials.

The supplied notes are evidence inputs, not a representation that the complete source papers were read by every model call. Historical card examples are editing examples, not factual sources for a new proposal.

## Runtime dependencies

LangGraph, LangChain, Streamlit and other dependencies are installed separately under their respective licenses. The model transport invokes the official OpenAI Codex CLI, installed and authenticated by the user. This source release does not distribute that CLI, account credentials or a Python runtime.
