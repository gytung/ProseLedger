"""Canonical whole-manuscript feedback-guided control; exactly three opportunities."""

from copy import deepcopy
import difflib
from . import pipeline
from .preservation import check_content_preservation
from .revision_prompts import targeted_prompt


def run_targeted(store, initial, sources, on_round=None):
    current = deepcopy(initial)
    versions = []
    folder = store.directory / "targeted"
    folder.mkdir(exist_ok=True)
    for round_no in (1, 2, 3):
        store.status(
            f"targeted_round_{round_no}",
            message=f"Targeted: rewrite, check and score round {round_no}/3.",
        )
        agent = f"targeted_rewriter_round_{round_no}"
        raw = store.ask(agent, targeted_prompt(current, sources))
        try:
            text = pipeline.normalize_six_sections(raw)
        except ValueError:
            text = raw
        guard = check_content_preservation(store, current["text"], text, sources)
        candidate = pipeline.evaluate_version(store, text, round_no, sources)
        accepted, selected = pipeline.select_candidate(current, candidate, guard)
        candidate.update(
            accepted=accepted,
            guard=guard,
            branch="targeted",
            effective_generator_agent=agent,
            prompt_has_retrieved_memory=False,
            prompt_has_local_memory=False,
            prompt_has_transfer_memory=False,
            previous_text_hash=current["text_hash"],
            original_text=current["text"],
            changed=text != current["text"],
            selected_score=selected["score"],
            selected_text_hash=selected["text_hash"],
            acceptance_reason=(
                "guard passed and combined score did not increase"
                if accepted
                else "fidelity/structure guard failed or combined score increased"
            ),
            diff="\n".join(
                difflib.unified_diff(
                    current["text"].splitlines(),
                    text.splitlines(),
                    fromfile="previous",
                    tofile="candidate",
                    lineterm="",
                )
            ),
        )
        pipeline.write_json(folder / f"round_{round_no}.json", candidate)
        (folder / f"round_{round_no}_candidate.md").write_text(text, encoding="utf-8", newline="\n")
        (folder / f"round_{round_no}_selected.md").write_text(
            selected["text"], encoding="utf-8", newline="\n"
        )
        versions.append(candidate)
        current = deepcopy(selected)
        if on_round:
            on_round(deepcopy(versions), deepcopy(current))
    return {"versions": versions, "final": current}
