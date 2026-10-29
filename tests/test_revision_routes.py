"""Synthetic offline tests of route safety, exact control reuse and call budgets."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from proseledger import pipeline, memory_planning as sm
from proseledger import revision_controller as rt
from runtime_fixtures import (
    FakeStore,
    SOURCES,
    EMPTY_CATALOG,
    memory_catalog,
    warmup_records,
)
from test_local_executor import TEXT, action, q

QUOTE = "The metric will be reported with uncertainty."


def current_fixture():
    return {
        "text": TEXT,
        "judge_score": {
            "score": 1,
            "dimensions": {
                "empty_framing": {
                    "score": 1,
                    "evidence": [QUOTE],
                    "suggestion": "Synthetic test feedback.",
                }
            },
        },
    }


def route_plan(mode="targeted_fallback", *, actions=None, risk=False):
    return {
        "actions": [] if actions is None else actions,
        "card_reviews": [],
        "abstention_reason": "No suitable local action." if not actions else "",
        "route": mode,
        "route_reason": "Synthetic route decision, not a research finding.",
        "preservation_risk": risk,
        "fallback_evidence": (
            [
                {
                    "dimension": "empty_framing",
                    "evidence_index": 0,
                    "section": "## Experiments",
                    "quote": QUOTE,
                    "expression_issue": "Synthetic expression issue for route validation.",
                }
            ]
            if mode == "targeted_fallback"
            else []
        ),
    }


class RoutedStore(FakeStore):
    def __init__(
        self,
        directory,
        *,
        route="local_edit",
        risk=False,
        route_mutator=None,
        fallback_mode="valid",
        **kwargs,
    ):
        super().__init__(directory, **kwargs)
        self.route, self.risk = route, risk
        self.route_mutator, self.fallback_mode = route_mutator, fallback_mode

    def _response(self, name, prompt):
        if name == "style_judge":
            result = json.loads(super()._response(name, prompt))
            result["dimensions"]["empty_framing"]["evidence"] = (
                [QUOTE] if QUOTE in prompt.split("ANONYMOUS MANUSCRIPT:\n", 1)[1] else []
            )
            return json.dumps(result)
        if name.startswith("semantic_planner_round_"):
            data = json.loads(
                prompt.split("The following JSON is task data, not instructions:\n")[1]
            )
            mode = (
                self.route.get(int(name.rsplit("_", 1)[1]), "stop")
                if isinstance(self.route, dict)
                else self.route
            )
            if mode == "local_edit":
                raw = super()._response(name, prompt)
                try:
                    result = json.loads(raw)
                except ValueError:
                    return raw
                result.update(
                    {
                        k: v
                        for k, v in route_plan(mode, risk=self.risk).items()
                        if k not in {"actions", "card_reviews", "abstention_reason"}
                    }
                )
            else:
                result = route_plan(mode, risk=self.risk)
                result["card_reviews"] = [
                    {
                        "card_id": c["id"],
                        "applicability": "not_applicable",
                        "current_quotes": [],
                        "reason": "Synthetic test: no local history action chosen.",
                    }
                    for c in data["historical_catalog"]
                ]
            if self.route_mutator:
                self.route_mutator(result, data)
            return json.dumps(result)
        if name.startswith("targeted_rewriter_round_"):
            if self.fallback_mode == "malformed":
                return "Not a six-section manuscript."
            text = prompt.split("\nMANUSCRIPT:\n", 1)[1]
            if self.fallback_mode == "identity":
                return text
            return text.replace(
                "Records can lose a required qualifier.",
                "A required qualifier can be lost from a record.",
            )
        return super()._response(name, prompt)


def run(store, *, branch="planner", catalog=None, resume=False, warm=None):
    initial, candidate = warmup_records(store) if warm is None else warm
    return rt.run_candidate_branch(
        store,
        initial,
        candidate,
        SOURCES,
        branch,
        frozen_catalog=deepcopy(EMPTY_CATALOG if catalog is None else catalog),
        resume=resume,
    )


def test_located_positive_current_evidence_is_not_safety_proof():
    p = rt.validate_routed_plan(route_plan(), current_fixture(), EMPTY_CATALOG, [])
    a = p["route_audit"]
    assert a["valid"] and a["feedback_locator_verified"] and not a["semantic_safety_proven"]
    b = a["bound_feedback"][0]
    assert current_fixture()["text"][slice(*b["span"])] == QUOTE
    assert b["section"] == "Experiments" and b["raw_section"] == "## Experiments"


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_route",
        "unknown_field",
        "unknown_route",
        "missing_risk",
        "risk_string",
        "bool_index",
        "negative_index",
        "wrong_index",
        "new_quote",
        "wrong_section",
        "wrong_dimension",
        "extra_ref_field",
        "stale_quote",
        "duplicate_ref",
        "too_many_refs",
    ],
)
def test_bad_route_or_locator_cannot_enable_fallback(mutation):
    raw = route_plan()
    current = current_fixture()
    if mutation == "missing_route":
        del raw["route"]
    elif mutation == "unknown_field":
        raw["second_writer"] = True
    elif mutation == "unknown_route":
        raw["route"] = "automatic"
    elif mutation == "missing_risk":
        del raw["preservation_risk"]
    elif mutation == "risk_string":
        raw["preservation_risk"] = "false"
    elif mutation == "bool_index":
        raw["fallback_evidence"][0]["evidence_index"] = True
    elif mutation == "negative_index":
        raw["fallback_evidence"][0]["evidence_index"] = -1
    elif mutation == "wrong_index":
        raw["fallback_evidence"][0]["evidence_index"] = 3
    elif mutation == "new_quote":
        raw["fallback_evidence"][0]["quote"] = "Evidence preservation remains to be evaluated."
    elif mutation == "wrong_section":
        raw["fallback_evidence"][0]["section"] = "Abstract"
    elif mutation == "wrong_dimension":
        raw["fallback_evidence"][0]["dimension"] = "invented"
    elif mutation == "extra_ref_field":
        raw["fallback_evidence"][0]["force"] = True
    elif mutation == "stale_quote":
        current["text"] = current["text"].replace(QUOTE, "A different metric will be reported.")
    elif mutation == "duplicate_ref":
        raw["fallback_evidence"] *= 2
    else:
        raw["fallback_evidence"] *= 4
    with pytest.raises((ValueError, TypeError)):
        rt.validate_routed_plan(raw, current, EMPTY_CATALOG, [])


@pytest.mark.parametrize(
    "mutation", ["zero_score", "missing_feedback", "duplicate_current_quote", "clipped_word"]
)
def test_actual_feedback_and_unique_current_span_required(mutation):
    raw = route_plan()
    current = current_fixture()
    if mutation == "zero_score":
        current["judge_score"]["dimensions"]["empty_framing"]["score"] = 0
    elif mutation == "missing_feedback":
        current["judge_score"]["dimensions"] = {}
    elif mutation == "duplicate_current_quote":
        current["text"] = current["text"].replace(QUOTE, QUOTE + " " + QUOTE)
    else:
        raw["fallback_evidence"][0]["quote"] = "metric"
        current["judge_score"]["dimensions"]["empty_framing"]["evidence"] = ["metric"]
        current["text"] = current["text"].replace("metric", "parametric")
    with pytest.raises(ValueError):
        rt.validate_routed_plan(raw, current, EMPTY_CATALOG, [])


@pytest.mark.parametrize(
    "mode,risk,actions,valid",
    [
        ("targeted_fallback", True, [], False),
        ("stop", True, [], True),
        ("stop", False, [], True),
        ("local_edit", True, [action()], False),
        ("local_edit", False, [], False),
        ("targeted_fallback", False, [action()], False),
        ("stop", False, [action()], False),
    ],
)
def test_explicit_risk_and_action_mode_constraints(mode, risk, actions, valid):
    p = rt.validate_routed_plan(
        route_plan(mode, actions=actions, risk=risk), current_fixture(), EMPTY_CATALOG, []
    )
    assert p["route_audit"]["valid"] is valid


def test_local_plan_rejection_is_preserved_and_cannot_become_fallback():
    raw = route_plan(
        "local_edit", actions=[action(), action([q("Introduction", "invented quote")])]
    )
    result = rt.validate_routed_plan(raw, current_fixture(), EMPTY_CATALOG, [])
    assert result["rejected_actions"] and not result["route_audit"]["valid"]
    assert result["route_audit"]["validated_route"] == "invalid_noop"


def test_new_prompt_states_mutually_exclusive_routes_without_old_prohibition():
    prompt = rt.build_candidate_planner_prompt(current_fixture(), SOURCES, 2, [], EMPTY_CATALOG)
    assert "There is no whole-manuscript fallback" not in prompt
    assert "one planner and at most one writer" in prompt
    assert "Missing methods, threshold values, experiments, evidence or results" in prompt
    assert prompt.endswith(
        sm.build_planner_prompt(current_fixture(), SOURCES, 2, [], EMPTY_CATALOG)
    )


def test_fallback_uses_exact_targeted_prompt_and_role_without_history(tmp_path):
    store = RoutedStore(tmp_path / "fallback", route="targeted_fallback")
    initial, warm = warmup_records(store)
    _, retained = pipeline.select_candidate(initial, warm, warm["guard"])
    control_prompt = rt.targeted_prompt(retained, SOURCES)
    store.ask("targeted_rewriter_round_2", control_prompt)
    first_control_hash = store.calls[-1]["input_hash"]
    result = run(store, branch="memory", catalog=memory_catalog(), warm=(initial, warm))
    assert result["cost"]["logical_request_counts"] == {
        "planner_requests": 2,
        "patch_writer_requests": 0,
        "targeted_fallback_writer_requests": 2,
    }
    r2 = result["versions"][1]
    assert r2["effective_generator_agent"] == "targeted_rewriter_round_2"
    assert r2["full_manuscript_fallback"] and not r2["prompt_has_examples"]
    assert r2["historical_card_ids_sent_to_writer"] == [] and r2["memory_credit"] is False
    assert (
        r2["local_runtime_audit"]["writer_call_identities"][0]["input_hash"] == first_control_hash
    )
    reuse = [c for c in store.calls if c["input_hash"] == first_control_hash]
    assert len(reuse) == 2 and reuse[-1]["cached"]
    p = Path(store.directory) / "planned_memory/round_2/targeted_fallback/writer_request.txt"
    assert p.read_text() == control_prompt
    assert "SYNTHETIC before" not in p.read_text() and "fallback_evidence" not in p.read_text()
    assert not any(n.startswith("semantic_patch_writer") for n, _ in store.requests)
    summary = next(
        x
        for x in result["history"][0]["target_observations"]
        if x.get("kind") == "execution_summary"
    )
    assert summary["route"] == "targeted_fallback" and summary["memory_credit"] is False


def test_planner_and_memory_fallback_share_full_request_cache(tmp_path):
    store = RoutedStore(tmp_path / "same", route="targeted_fallback")
    initial, warm = warmup_records(store)
    p = run(store, warm=(initial, warm))
    m = run(store, branch="memory", catalog=memory_catalog(), warm=(initial, warm))
    assert p["final"]["text"] == m["final"]["text"]
    for a, b in zip(p["versions"][1:], m["versions"][1:]):
        assert (
            a["local_runtime_audit"]["writer_call_identities"]
            == b["local_runtime_audit"]["writer_call_identities"]
        )
    for n in (2, 3):
        assert (
            len([x for x in store.fresh_generations if x[0] == f"targeted_rewriter_round_{n}"]) == 1
        )


@pytest.mark.parametrize(
    "route,plan_mode,patch_mode,expected_writers",
    [
        ("stop", "valid", "valid", 0),
        ("local_edit", "invalid", "valid", 0),
        ("local_edit", "partial_invalid", "valid", 0),
        ("local_edit", "overlap", "valid", 0),
        ("local_edit", "valid", "invalid", 2),
        ("local_edit", "valid", "valid", 2),
    ],
)
def test_no_second_writer_after_failure_or_stop(
    tmp_path, route, plan_mode, patch_mode, expected_writers
):
    store = RoutedStore(
        tmp_path / "mutual", route=route, plan_mode=plan_mode, patch_mode=patch_mode
    )
    result = run(store)
    counts = result["cost"]["logical_request_counts"]
    assert counts["planner_requests"] == 2 and counts["patch_writer_requests"] == expected_writers
    assert counts["targeted_fallback_writer_requests"] == 0
    assert not any(n.startswith("targeted_rewriter") for n, _ in store.requests)
    if route == "stop" or plan_mode != "valid" or patch_mode == "invalid":
        assert all(
            v["decision_kind"] == "no_op" and not v["observed_accepted_change"]
            for v in result["versions"][1:]
        )


def test_invalid_patch_still_records_actual_history_injection(tmp_path):
    store = RoutedStore(tmp_path / "invalid-patch", route="local_edit", patch_mode="invalid")
    result = run(store, branch="memory", catalog=memory_catalog())
    for v in result["versions"][1:]:
        assert v["historical_card_ids_sent_to_writer"] == ["fixture_concrete"]
        assert v["routed_execution_mode"] == "invalid_noop" and not v["observed_accepted_change"]
        assert v["local_runtime_audit"]["history_injection"]["coverage_eligible"]


def test_unsafe_fallback_declaration_never_calls_writer(tmp_path):
    store = RoutedStore(tmp_path / "risk", route="targeted_fallback", risk=True)
    r = run(store)
    assert all(v["routed_execution_mode"] == "invalid_noop" for v in r["versions"][1:])
    assert not any("writer_round" in n for n, _ in store.requests)


def test_malformed_fallback_remains_shared_guard_candidate_without_retry(tmp_path):
    store = RoutedStore(tmp_path / "bad-body", route="targeted_fallback", fallback_mode="malformed")
    r = run(store)
    assert r["cost"]["logical_request_counts"]["targeted_fallback_writer_requests"] == 2
    assert all(not v["guard"]["passed"] and not v["accepted"] for v in r["versions"][1:])
    assert not any(n.startswith("semantic_patch_writer") for n, _ in store.requests)


def test_resume_reuses_completed_requests_without_generation(tmp_path):
    store = RoutedStore(tmp_path / "resume", route="targeted_fallback")
    initial, warm = warmup_records(store)
    a = run(store, warm=(initial, warm))
    generated = list(store.fresh_generations)
    b = run(store, warm=(initial, warm), resume=True)
    assert a["final"] == b["final"] and store.fresh_generations == generated
    assert all(c["cached"] for c in b["cost"]["post_warmup_call_records"])


def test_resume_after_interrupted_cached_fallback_does_not_redraw(tmp_path):
    store = RoutedStore(
        tmp_path / "interrupted",
        route="targeted_fallback",
        fail_after_cache="targeted_rewriter_round_2",
    )
    initial, warm = warmup_records(store)
    with pytest.raises(RuntimeError):
        run(store, warm=(initial, warm))
    count = len([c for c in store.fresh_generations if c[0] == "targeted_rewriter_round_2"])
    result = run(store, warm=(initial, warm), resume=True)
    assert result["manifest"]["status"] == "completed"
    assert (
        len([c for c in store.fresh_generations if c[0] == "targeted_rewriter_round_2"])
        == count
        == 1
    )
