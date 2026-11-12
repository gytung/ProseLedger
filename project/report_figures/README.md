# Reproduce the report figures

Four entry points render the complete **17-figure** set from the bundled evidence. They make no model or detector calls and require no API key.

Install the optional plotting dependencies:

```sh
python -m pip install "matplotlib>=3.8,<4" "numpy>=1.26,<3"
```

From the project root, run:

```sh
python report_figures/draw_mechanisms.py
python report_figures/draw_results.py
python report_figures/draw_strategy.py
python report_figures/draw_interface_evidence.py
```

Use `python3` on macOS if required. PDF, SVG and PNG outputs are written under `report_figures/assets/`. Diagrams and charts use a publication-width layout; PDFs embed vector shapes and fonts, and SVG text remains editable. The interface figure also contains a raster screenshot of the actual application.

| Entry point | Figures and source evidence |
|---|---|
| `draw_mechanisms.py` | Five figures: evidence-bound architecture, the C01 decision trace, six editorial operations, the paired evaluation design and deployment routes. C01 and the frozen 12-case/72-fact input set are checked before rendering. Editorial examples are explicitly illustrative. |
| `draw_results.py` | Eight figures: archived Mac MLX pilot, human response summaries, preservation challenge, paired GPTZero observations, order-reversed naturalness preferences, section retention paths, resource use, and case-level diagnostics. Every recorded case is included. |
| `draw_strategy.py` | Three figures: proposed applications, adaptation architecture and economic sensitivity. `strategy_figure_data.json` separates proposed pilots and assumed costs from observed results. |
| `draw_interface_evidence.py` | One figure combining the real desktop interface, the C01 section word counts and the rejected-repair trace. It uses the preserved C01 Rules run and `reference_ui/desktop_candidate_narrow.png`. |

The screenshot displays an existing, completed execution in the real application. Capturing or rendering this view makes **zero new inference calls**. It is not evidence of a newly generated output. The figure checks the recorded 379 initial words, 374 retained words, five changed sections, six local writer calls and the restored limitation section. The bundled capture provenance and generated data manifest bind the image and records with SHA-256 hashes.

`style.py` supplies typography, colours and vector glyphs. Times New Roman and Comic Sans MS are used when available, with DejaVu fallbacks. Font caches use the operating system's temporary directory. No font installation or private local path is needed. Agent glyphs are custom illustrations, not official provider logos.

`draw_paired_figures.py` is retained as the strict evidence loader used by the results renderer. Check the complete paired study without plotting:

```sh
python report_figures/draw_paired_figures.py --evaluation evaluation --check-only
```

The loader checks completed runs, text hashes, reversed presentation orders and summary agreement. Missing observations are never replaced by zero. The detector chart preserves the full 0–100% scale; model preferences are labelled as an LLM proxy, separately from human responses. Generated provenance JSON records the supporting hashes and numeric assertions without storing a machine-specific path.

Optional input and output locations:

```sh
python report_figures/draw_mechanisms.py --evaluation evaluation --output-dir report_figures/assets
python report_figures/draw_results.py --evaluation evaluation --output report_figures/assets
python report_figures/draw_strategy.py --data report_figures/strategy_figure_data.json --output-dir report_figures/assets/strategy
python report_figures/draw_interface_evidence.py --evaluation evaluation --captures report_figures/reference_ui --output report_figures/assets/extra
```

The four entry points above produce the report layout. Use the paired loader's `--check-only` mode rather than its legacy plotting mode, which renders an earlier layout under the same result filenames. The scripts were rendered with Matplotlib 3.10.8; inspect typography after font substitution on another machine.
