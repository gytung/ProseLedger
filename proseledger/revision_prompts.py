from copy import deepcopy
import json

TARGETED_INSTRUCTION = "Rewrite the entire manuscript to read more naturally while preserving its content.\nPreserve its six exact section headings, all [S1]-style citations, numbers, technical terminology,\nnegations, evidence limits, uncertainty and planned status. Do not invent facts or empirical results.\nWhen the manuscript omits a design detail, do not invent it or add a new claim that it is\nundefined, untested or still to be specified. Preserve only limitations and project-status\nstatements already supported by the manuscript. Improve the expression of existing content.\nKeep a similar length; do not obtain a lower style score by deleting substantive content.\nReturn only the complete manuscript. No commentary or reasoning.\n"
SPECIFIC_INSTRUCTION = "Use these specific detector findings and rubric suggestions to remove actual stylistic problems while keeping the scientific meaning intact. No change is required where no problem is supported.\n"


def targeted_prompt(current, sources, addition=""):
    prompt = TARGETED_INSTRUCTION
    prompt += SPECIFIC_INSTRUCTION
    prompt += (
        json.dumps(
            {"rule_findings": current["rule_score"], "rubric_findings": current["judge_score"]},
            ensure_ascii=False,
        )
        + "\n"
    )
    if addition:
        prompt += addition + "\n"
    return (
        prompt
        + "SUPPLIED EVIDENCE (not permission to add new claims):\n"
        + json.dumps(sources, ensure_ascii=False)
        + "\nMANUSCRIPT:\n"
        + current["text"]
    )


def _history_record(round_number, plan, previous, candidate, selected):
    observations = []
    for action in plan.get("actions", []):
        for target in action.get("targets", []):
            quote = target.get("quote", "")
            observations.append(
                {
                    "section": target.get("section"),
                    "quote": quote,
                    "original_quote_still_present": quote in candidate["text"],
                    "note": "Literal persistence only; absence does not prove the planned operation was executed.",
                }
            )
    return {
        "round": round_number,
        "actions": deepcopy(plan.get("actions", [])),
        "accepted": candidate["accepted"],
        "guard_passed": candidate["guard"]["passed"],
        "guard_issues": deepcopy(candidate["guard"].get("issues", [])),
        "semantic_verdict": candidate["guard"].get("semantic_audit", {}).get("verdict"),
        "score_before": previous["score"]["score"],
        "score_after": candidate["score"]["score"],
        "selected_score": selected["score"]["score"],
        "previous_text_hash": previous["text_hash"],
        "candidate_text_hash": candidate["text_hash"],
        "selected_text_hash": selected["text_hash"],
        "target_observations": observations,
        "interpretation": "Observed branch-local outcome, not causal credit or a verified factual-error label.",
    }
