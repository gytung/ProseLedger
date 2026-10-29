"""Boundary and atomicity tests on invented text; no model, bank, or test manuscript."""

from copy import deepcopy
import json

import pytest

from proseledger import memory_planning as sm
from proseledger.local_executor import (
    ContractError,
    VERSION,
    MAX_REPLACEMENT_CHARS,
    apply_patch_response,
    build_writer_prompt,
    compile_edit_contract,
    complete_attempt,
    prepare_attempt,
    sha256,
)

TEXT = """## Abstract
This proposal compares two record formats. Evaluation is planned, not completed.

## Introduction
Records can lose a required qualifier. We will examine two formats [S1].

This paragraph is outside all edit targets.

## Related Work
Existing systems record provenance [S1]. Their results do not establish this proposal's outcome.

## Methodology
The study will compare formats on the same tasks. The threshold is fixed at 16 GB.

## Experiments
No experiment has been conducted. The metric will be reported with uncertainty.

## Conclusion
This work is a proposal. Evidence preservation remains to be evaluated.
"""


def q(section, quote):
    return {"section": section, "quote": quote}


def action(targets=None, *, preserve=None, kind="rewrite", survivor=None):
    targets = targets or [q("Introduction", "Records can lose a required qualifier.")]
    preserve = preserve or [q("Abstract", "Evaluation is planned, not completed.")]
    return {
        "dimension": "repetitive_structure" if kind == "consolidate" else "empty_framing",
        "operation_type": kind,
        "targets": targets,
        "operation": "Improve only the identified expression while retaining its meaning.",
        "preserve": [{**x, "reason": "Retain this existing qualification."} for x in preserve],
        "memory_card_ids": [],
        "condition_checks": [],
        "correspondence": {
            "relation": "same_proposition" if kind == "consolidate" else "local_expression",
            "current_pattern": "Existing content can be expressed more directly.",
            "mappings": [
                {
                    "target_index": i,
                    "proposition": "An existing proposal statement.",
                    "scope": "Prospective, with original evidence limits.",
                }
                for i in range(len(targets))
            ],
            "retained_at": survivor,
        },
    }


def plan(*actions, text=TEXT):
    return sm.validate_plan(
        {
            "actions": list(actions),
            "card_reviews": [],
            "abstention_reason": "No safe edit." if not actions else "",
        },
        {"text": text},
        {"cards": []},
        [],
    )


def patch(contract, replacements=None):
    replacements = (
        replacements
        if replacements is not None
        else {w["target_id"]: w["before"] for w in contract["windows"]}
    )
    return {
        "schema_version": VERSION,
        "base_sha256": contract["base_sha256"],
        "contract_sha256": contract["contract_sha256"],
        "edits": [
            {
                "target_id": w["target_id"],
                "before": w["before"],
                "replacement": replacements[w["target_id"]],
            }
            for w in contract["windows"]
            if w["target_id"] in replacements
        ],
    }


def apply(text, contract, payload):
    return apply_patch_response(text, contract, json.dumps(payload, ensure_ascii=False))


def assert_noop(result, text=TEXT):
    assert not result["valid"] and not result["changed"]
    assert result["text"].encode("utf-8") == text.encode("utf-8")
    assert result["candidate_sha256"] == sha256(text)
    assert result["issues"] and not result["retry_allowed"]
    assert result["applied_edits"] == []


def test_valid_local_rewrite_preserves_every_outside_byte_and_heading():
    contract = compile_edit_contract(TEXT, plan(action()))
    assert len(contract["windows"]) == 1
    window = contract["windows"][0]
    assert (
        window["before"]
        == "Records can lose a required qualifier. We will examine two formats [S1]."
    )
    replacement = (
        "A required qualifier can be lost from a record. We will examine two formats [S1]."
    )
    result = apply(TEXT, contract, patch(contract, {window["target_id"]: replacement}))
    assert result["valid"] and result["changed"]
    assert result["text"] == TEXT[: window["start"]] + replacement + TEXT[window["end"] :]
    assert result["audit"]["outside_authorized_regions_byte_identical"]
    assert not result["semantic_fidelity_proven"]


def test_no_judge_keyword_gate_sparse_original_ids_and_same_action_paragraph_dedup():
    a = action(
        [
            q("Introduction", "Records can lose a required qualifier."),
            q("Introduction", "We will examine two formats [S1]."),
        ]
    )
    validated = plan(a)
    validated["actions"][0]["id"] = "action_2"
    contract = compile_edit_contract(TEXT, validated)
    assert len(contract["windows"]) == 1
    assert contract["windows"][0]["target_indices"] == [0, 1]
    assert contract["groups"][0]["action_id"] == "action_2"
    assert contract["windows"][0]["target_id"].startswith("action_2-")


def test_disjoint_quotes_in_same_paragraph_cannot_expand_across_actions():
    validated = plan(action(), action([q("Introduction", "We will examine two formats [S1].")]))
    assert len(validated["actions"]) == 2  # Admitted by the real V10 validator.
    with pytest.raises(ContractError, match="overlaps another action"):
        compile_edit_contract(TEXT, validated)


@pytest.mark.parametrize("mutation", ["span", "sha", "section", "plan_hash", "duplicate_action"])
def test_compiler_rejects_forged_validated_fields(mutation):
    validated = plan(action())
    target = validated["actions"][0]["targets"][0]
    if mutation == "span":
        target["span"][0] += 1
    elif mutation == "sha":
        target["sha256"] = "0" * 64
    elif mutation == "section":
        target["section"] = "Abstract"
    elif mutation == "plan_hash":
        validated["current_text_sha256"] = "0" * 64
    else:
        validated["actions"].append(deepcopy(validated["actions"][0]))
    with pytest.raises((ContractError, ValueError)):
        compile_edit_contract(TEXT, validated)


def test_complete_paragraph_budget_rejects_without_clipping():
    long_text = TEXT.replace(
        "Records can lose a required qualifier.",
        "Records can lose a required qualifier. " + "x" * 7001,
    )
    validated = plan(action(), text=long_text)
    with pytest.raises(ContractError, match="Complete paragraphs exceed"):
        compile_edit_contract(long_text, validated)


@pytest.mark.parametrize(
    "mutation",
    [
        "base_hash",
        "contract_hash",
        "unknown_id",
        "duplicate_id",
        "before",
        "coordinates",
        "top_extra",
        "empty",
        "heading",
        "blank_line",
        "oversized",
    ],
)
def test_invalid_last_patch_never_partially_applies(mutation):
    validated = plan(
        action(), action([q("Methodology", "The study will compare formats on the same tasks.")])
    )
    contract = compile_edit_contract(TEXT, validated)
    payload = patch(contract)
    payload["edits"][0][
        "replacement"
    ] = "Records may lose a required qualifier. We will examine two formats [S1]."
    last = payload["edits"][-1]
    if mutation == "base_hash":
        payload["base_sha256"] = "0" * 64
    elif mutation == "contract_hash":
        payload["contract_sha256"] = "0" * 64
    elif mutation == "unknown_id":
        last["target_id"] = "not-authorized"
    elif mutation == "duplicate_id":
        last["target_id"] = payload["edits"][0]["target_id"]
    elif mutation == "before":
        last["before"] += " "
    elif mutation == "coordinates":
        last["start"] = 0
    elif mutation == "top_extra":
        payload["full_manuscript"] = "not permitted"
    elif mutation == "empty":
        last["replacement"] = ""
    elif mutation == "heading":
        last["replacement"] = "## Unapproved heading"
    elif mutation == "blank_line":
        last["replacement"] = "First paragraph.\n\nSecond paragraph."
    else:
        last["replacement"] = "x" * (MAX_REPLACEMENT_CHARS + 1)
    assert_noop(apply(TEXT, contract, payload))


def test_duplicate_json_keys_and_full_draft_are_noop():
    contract = compile_edit_contract(TEXT, plan(action()))
    raw = json.dumps(patch(contract))
    raw = raw[:-1] + ', "edits": []}'
    assert_noop(apply_patch_response(TEXT, contract, raw))
    assert_noop(apply_patch_response(TEXT, contract, TEXT))


def test_response_order_and_changed_lengths_use_original_coordinates():
    contract = compile_edit_contract(
        TEXT,
        plan(
            action(),
            action([q("Methodology", "The study will compare formats on the same tasks.")]),
        ),
    )
    payload = patch(contract)
    payload["edits"][0][
        "replacement"
    ] = "We will examine two formats [S1] because records can lose a required qualifier."
    payload["edits"][1][
        "replacement"
    ] = "Formats will be compared on the same tasks. The threshold is fixed at 16 GB."
    forward = apply(TEXT, contract, payload)
    payload["edits"].reverse()
    reverse = apply(TEXT, contract, payload)
    assert forward["valid"] and reverse["valid"] and forward["text"] == reverse["text"]
    assert "This paragraph is outside all edit targets." in forward["text"]


def test_compiled_window_tampering_is_noop_even_with_unmodified_plan():
    contract = compile_edit_contract(TEXT, plan(action()))
    response = patch(contract)
    contract["windows"][0]["start"] = 0
    assert_noop(apply(TEXT, contract, response))


def test_utf8_and_crlf_are_bound_without_normalization():
    text = TEXT.replace("This paragraph", "\u4e2d\u6587 café e\u0301 — This paragraph").replace(
        "\n", "\r\n"
    )
    contract = compile_edit_contract(text, plan(action(), text=text))
    payload = patch(contract)
    result = apply(text, contract, payload)
    assert result["valid"] and result["text"].encode() == text.encode()
    changed = text.replace("e\u0301", "é")
    assert_noop(apply(changed, contract, payload), changed)


CONSOLIDATION = """## Abstract
There is no evidence from deployment. This is a proposal.

## Introduction
There is no evidence from deployment. The benchmark uses 16 GB [S1].

## Methodology
There is no evidence from deployment. Evaluation is planned.

## Conclusion
This untouched paragraph also says: Evaluation is planned.
"""


def consolidation_plan(*extra):
    targets = [
        q(section, "There is no evidence from deployment.")
        for section in ["Abstract", "Introduction", "Methodology"]
    ]
    a = action(
        targets,
        kind="consolidate",
        survivor=targets[2],
        preserve=[
            q("Abstract", "This is a proposal."),
            q("Introduction", "The benchmark uses 16 GB [S1]."),
            q("Methodology", "Evaluation is planned."),
        ],
    )
    return plan(a, *extra, text=CONSOLIDATION)


def test_consolidation_keeps_survivor_and_unique_declared_constraints():
    contract = compile_edit_contract(CONSOLIDATION, consolidation_plan())
    payload = patch(contract)
    payload["edits"][0]["replacement"] = "This is a proposal."
    payload["edits"][1]["replacement"] = "The benchmark uses 16 GB [S1]."
    result = apply(CONSOLIDATION, contract, payload)
    assert result["valid"] and result["changed"]
    assert result["text"].count("There is no evidence from deployment.") == 1


@pytest.mark.parametrize(
    "mutation", ["partial", "move_survivor", "drop_unique", "other_section_copy"]
)
def test_consolidation_constraints_apply_at_original_location(mutation):
    contract = compile_edit_contract(CONSOLIDATION, consolidation_plan())
    payload = patch(contract)
    if mutation == "partial":
        payload["edits"].pop()
    elif mutation == "move_survivor":
        payload["edits"][2]["replacement"] = "Evaluation is planned."
    elif mutation == "drop_unique":
        payload["edits"][1]["replacement"] = "There is no evidence from deployment."
    else:
        payload["edits"][2]["replacement"] = "There is no evidence from deployment."
    assert_noop(apply(CONSOLIDATION, contract, payload), CONSOLIDATION)


def test_consolidation_lock_applies_to_another_actions_modified_paragraph():
    text = CONSOLIDATION
    targets = [
        q(section, "There is no evidence from deployment.")
        for section in ["Abstract", "Introduction"]
    ]
    first = action(
        targets,
        kind="consolidate",
        survivor=targets[0],
        preserve=[q("Methodology", "Evaluation is planned.")],
    )
    second = action(
        [q("Methodology", "There is no evidence from deployment.")],
        preserve=[q("Abstract", "This is a proposal.")],
    )
    contract = compile_edit_contract(text, plan(first, second, text=text))
    payload = patch(contract)
    payload["edits"][-1]["replacement"] = "There is no evidence from deployment."
    assert_noop(apply(text, contract, payload), text)


def test_ordinary_preserve_is_semantic_not_falsely_certified_by_executor():
    a = action(preserve=[q("Introduction", "Records can lose a required qualifier.")])
    contract = compile_edit_contract(TEXT, plan(a))
    payload = patch(contract)
    payload["edits"][0][
        "replacement"
    ] = "A record may lose a required qualifier. We will examine two formats [S1]."
    result = apply(TEXT, contract, payload)
    assert result["valid"] and result["requires_shared_fidelity_and_scoring"]
    assert not result["semantic_fidelity_proven"]


def test_request_is_patch_only_and_artifacts_keep_exact_bytes(tmp_path):
    validated = plan(action())
    contract = compile_edit_contract(TEXT, validated)
    prompt = build_writer_prompt(TEXT, contract, [{"key": "S1", "content": "Fixture evidence."}])
    assert "Do not return a full manuscript" in prompt and "read_only_manuscript" in prompt
    directory = tmp_path / "attempt"
    prepared = prepare_attempt(
        directory,
        TEXT,
        validated,
        [],
        planner_request="exact\r\nrequest",
        planner_response=' {"offline_fixture": true} ',
    )
    assert prepared["writer_call_allowed"]
    assert (directory / "writer_request.txt").read_bytes() == prepared["writer_request"].encode()
    assert (directory / "planner_request.txt").read_bytes() == b"exact\r\nrequest"
    raw = " \n" + json.dumps(patch(contract)) + "\n "
    result = complete_attempt(directory, raw)
    assert result["valid"] and (directory / "writer_response.txt").read_bytes() == raw.encode()
    with pytest.raises(ContractError, match="already completed"):
        complete_attempt(directory, raw)
    with pytest.raises(FileExistsError):
        prepare_attempt(directory, TEXT, validated, [])


def test_only_selected_synthetic_history_is_in_the_writer_request():
    def card(card_id, marker):
        return {
            "id": card_id,
            "dimensions": ["empty_framing"],
            "operation": "Use an existing concrete statement.",
            "steps": ["A concrete statement already exists."],
            "preserve": ["Original meaning"],
            "conditions": [
                {"id": "R1", "kind": "required", "text": "A concrete statement exists."}
            ],
            "counterexamples": [],
            "examples": [
                {
                    "episode_id": "synthetic-fixture-" + card_id,
                    "payload": {
                        "before": marker + " old [S1]",
                        "after": marker + " edited [S1]",
                        "label": "synthetic unit-test example, not observed evidence",
                    },
                }
            ],
        }

    catalog = {
        "cards": [
            card("selected_fixture", "SELECTED_FIXTURE"),
            card("unused_fixture", "UNSELECTED_FIXTURE"),
        ]
    }
    a = action()
    target = a["targets"][0]
    a["memory_card_ids"] = ["selected_fixture"]
    a["correspondence"]["historical_pattern"] = "The existing statement can be expressed directly."
    a["condition_checks"] = [
        {
            "condition_id": "R1",
            "status": "supported",
            "evidence": [target],
            "reason": "The supplied current sentence is concrete.",
        }
    ]
    raw = {
        "actions": [a],
        "abstention_reason": "",
        "card_reviews": [
            {
                "card_id": "selected_fixture",
                "applicability": "applicable",
                "current_quotes": [target],
                "reason": "Synthetic binding for this offline interface test.",
            }
        ],
    }
    validated = sm.validate_plan(raw, {"text": TEXT}, catalog, [])
    assert len(validated["actions"]) == 1
    contract = compile_edit_contract(TEXT, validated, catalog)
    prompt = build_writer_prompt(TEXT, contract, [])
    assert "SELECTED_FIXTURE" in prompt and "UNSELECTED_FIXTURE" not in prompt
    assert "[HIST_S1]" in prompt


def test_invalid_raw_patch_is_saved_and_completed_as_noop(tmp_path):
    directory = tmp_path / "invalid-patch"
    prepare_attempt(directory, TEXT, plan(action()), [])
    raw = "  This is a full rewritten manuscript, not an admissible patch.\r\n"
    result = complete_attempt(directory, raw)
    assert_noop(result)
    assert (directory / "writer_response.txt").read_bytes() == raw.encode()
    assert (directory / "candidate.md").read_bytes() == TEXT.encode()
    assert json.loads((directory / "execution_result.json").read_bytes())["retry_allowed"] is False


def test_empty_plan_and_compile_failure_never_request_writer(tmp_path):
    directory = tmp_path / "empty"
    result = prepare_attempt(directory, TEXT, plan(), [])
    assert not result["writer_call_allowed"]
    saved = json.loads((directory / "execution_result.json").read_bytes())
    assert not saved["changed"] and "no writer response" in saved["response_source"]
    assert not (directory / "writer_response.txt").exists()
    invalid = plan(action())
    invalid["current_text_sha256"] = "0" * 64
    directory = tmp_path / "invalid"
    result = prepare_attempt(directory, TEXT, invalid, [])
    assert not result["compiler_valid"] and not result["writer_call_allowed"]
    assert (directory / "candidate.md").read_bytes() == TEXT.encode()
    assert not (directory / "writer_request.txt").exists()
