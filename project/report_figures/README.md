# Reproduce the report figures

These scripts render publication figures from the included evidence and documented design specifications. They do not call a model or a detector, and they require no API key.

Install the optional plotting dependencies:

```sh
python -m pip install "matplotlib>=3.8,<4" "numpy>=1.26,<3"
```

Run these commands from the project root. On macOS, use `python3` if needed.

```sh
python report_figures/draw_figures.py
python report_figures/draw_extra_figures.py
python report_figures/draw_paired_figures.py
python report_figures/draw_strategy_figures.py
```

PDF, SVG and PNG files are written to `report_figures/assets/`. PDFs preserve vector graphics and embed fonts; SVG text remains editable. Times New Roman is used when installed, with DejaVu Serif as the fallback. Selected flow labels use Comic Sans MS when available, or DejaVu Sans. Font caches use the operating system's temporary directory. No font installation or local account path is required.

| Script | Output and evidence |
|---|---|
| `draw_figures.py` | Core architecture, the four-case archived Mac MLX pilot, the two ten-response human summaries and the known-answer preservation challenge. The published table values are encoded in this script; the corresponding source records are in `research/qwen_mlx/archive/` and `evaluation/`. |
| `draw_extra_figures.py` | Six editorial operations, the recorded C01 decision trace, the paired evaluation design and deployment routes. C01 and input-count assertions are checked against adjacent `evaluation/` files. Editorial examples are illustrative. |
| `draw_paired_figures.py` | All 36 case–condition GPTZero observations, both presentation orders of all 12 preference judgments, and the final retention paths of all 144 sections. The script validates completeness, text hashes and summary agreement before plotting. |
| `draw_strategy_figures.py` | Proposed application routes, adaptation architecture and cost sensitivity. `strategy_figure_data.json` distinguishes proposed pilot designs and illustrative financial assumptions from measured findings. |

To check or plot a separate completed paired evaluation:

```sh
python report_figures/draw_paired_figures.py --evaluation evaluation --check-only
python report_figures/draw_paired_figures.py --evaluation evaluation --output report_figures/assets/paired
```

`figure_data.json` beside the paired figures records the plotted values and hashes of their supporting files. Missing observations are not filled with zero. The detector chart always retains the full 0–100% probability scale, including when all outputs equal 100%. The preference chart reports model judgments as an LLM proxy, separate from human responses.

The scripts were rendered with Matplotlib 3.10.8 on macOS. Font substitution may change line widths on other machines; the vector text can be adjusted before publication without changing the plotted data.
