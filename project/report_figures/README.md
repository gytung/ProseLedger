# Reproduce the report figures

The three commands below reproduce the complete 14-figure set used in the final reports. They read the bundled evidence, do not call a model or detector, and need no API key.

Install the optional plotting dependencies:

```sh
python -m pip install "matplotlib>=3.8,<4" "numpy>=1.26,<3"
```

Run from the project root. On macOS, use `python3` if needed.

```sh
python report_figures/draw_mechanisms.py
python report_figures/draw_results.py
python report_figures/draw_strategy.py
```

Outputs are vector PDF, editable-text SVG and PNG files under `report_figures/assets/`. Fonts fall back from Times New Roman and Comic Sans MS to DejaVu Serif and DejaVu Sans when necessary. The font cache uses the operating system's temporary directory. No font download, private path, login or local model is required.

| Entry point | Figures and evidence |
|---|---|
| `draw_mechanisms.py` | Five mechanism figures: current architecture, recorded C01 decision trace, six illustrative editorial operations, paired evaluation design and deployment routes. It checks the C01 ledger and the frozen 12-case/72-fact input set before rendering. |
| `draw_results.py` | Six result figures: the archived four-case Mac MLX pilot, public human responses, known-answer preservation challenge, all 36 paired GPTZero observations, both presentation orders of all 12 preference judgments, and all 144 section-retention paths. |
| `draw_strategy.py` | Three strategy figures: proposed application routes, adaptation architecture and cost sensitivity. `strategy_figure_data.json` distinguishes proposed pilot designs and assumed financial scenarios from measured results. |

`style.py` provides the shared typography, palette and vector glyphs. Agent and model glyphs are original illustrations, not official provider logos. Each mechanism figure records only implemented behavior: section editing, bounded repair, verification and the per-run ledger. It does not imply historical-card retrieval. GPTZero is shown as a post-retention observation.

The results renderer imports the strict evidence loader in `draw_paired_figures.py`; use its `--check-only` command for evidence validation. The loader checks completion, text hashes, both presentation orders and summary agreement. It writes the checked values and supporting file hashes to `assets/paired/figure_data.json`. Missing values are never replaced by zero. Detector charts retain the full 0–100% scale, including when every observation equals 100%; model preferences remain labelled as an LLM proxy, separate from human responses.

Optional paths:

```sh
python report_figures/draw_mechanisms.py --evaluation evaluation --output-dir report_figures/assets
python report_figures/draw_results.py --evaluation evaluation --output report_figures/assets
python report_figures/draw_strategy.py --data report_figures/strategy_figure_data.json --output-dir report_figures/assets/strategy
python report_figures/draw_paired_figures.py --evaluation evaluation --check-only
```


The final figures were rendered with Matplotlib 3.10.8. Font substitution can change text widths; inspect the exported pages when preparing a publication on another machine. Altering layout does not change the recorded data.
