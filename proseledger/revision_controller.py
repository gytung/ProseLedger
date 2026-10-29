"""The current explicit-route revision controller; one planner, at most one writer."""

from __future__ import annotations
from copy import deepcopy
import difflib
import json
from pathlib import Path
from uuid import uuid4
from . import pipeline, memory_planning as sm, preservation as revision_verifier
from .revision_prompts import _history_record, targeted_prompt
from . import local_executor as executor
from .checkpoints import (
    _need,
    _finite,
    verify_shared_warmup,
    _ensure_bytes,
    _ensure_json,
    _call_identities,
    _cache_record,
    _ask_once,
    _prepare_patch_checkpoint,
    _cost,
    _record_failure,
)

VERSION = "v12-explicit-route-shared-warmup-1"
ROUTE_VERSION = "v12-judge-grounded-route-1"
ROUTE_FIELDS = {"route", "route_reason", "preservation_risk", "fallback_evidence"}
PLAN_FIELDS = {"actions", "card_reviews", "abstention_reason"}
EVIDENCE_FIELDS = {"dimension", "evidence_index", "section", "quote", "expression_issue"}
ROUTED_PLANNER_CONTRACT = 'Explicit writer-route contract, common to both planning arms:\nChoose exactly one route BEFORE any writer call: local_edit, targeted_fallback, or stop. Add the following four top-level fields to the JSON schema below; no other top-level fields are allowed:\n"route": "local_edit|targeted_fallback|stop",\n"route_reason": "brief public reason for this writer choice",\n"preservation_risk": false,\n"fallback_evidence": [{"dimension":"an existing judge dimension", "evidence_index":0, "section":"exact current heading", "quote":"exact existing judge evidence string, also verbatim in the current section", "expression_issue":"brief explanation of the remaining expression problem using existing content only"}].\nlocal_edit requires one or more fully valid actions, preservation_risk=false, and fallback_evidence=[]. Every exact target quotation authorizes replacement of its complete ORIGINAL paragraph only. Different actions MUST NOT share a containing paragraph. All distinct authorized original paragraphs together must be at most 7000 characters. No other paragraph, heading or section can change. Each replacement remains one paragraph; empty replacement is allowed only for consolidation. For consolidation, the retained_at survivor and every preserve quote remain verbatim in their ORIGINAL paragraphs. Cross-paragraph edits require all affected paragraphs targeted within the same action.\ntargeted_fallback requires actions=[], preservation_risk=false, and 1 to 3 fallback_evidence entries. Each must identify a positive-score CURRENT judge dimension and its zero-based evidence index; quote must equal that exact feedback string AND be uniquely present within one current paragraph of the specified section. Do not invent or expand a judge quotation, use previous feedback, or cite catalog text. If exact evidence is absent, fallback is unavailable. This route uses the ordinary Targeted writer, with its original full-manuscript prompt and no plan, catalog or historical examples; it receives no historical-operation credit.\nUse targeted_fallback when no suitable grounded local plan is selected but the current judge still identifies a locatable EXPRESSION problem that can be addressed without changing scientific content. Missing methods, threshold values, experiments, evidence or results are not expression problems to fill in. No applicable historical card is NOT proof that no ordinary edit is possible. A rejected card or unsafe proposed consolidation does not by itself make all expression changes unsafe. Conversely, the existence of a judge quotation is not proof that an edit is safe.\nstop requires actions=[] and fallback_evidence=[]. Use preservation_risk=true when ordinary rewriting would risk an unresolved change to claims, conditions, sources or evidential status; otherwise use stop with false when no supported remaining expression issue is identified. Explain the concrete reason. Do not relabel a safety abstention as fallback just to use a remaining opportunity. For empty actions, abstention_reason explains why NO LOCAL PLAN is selected, not necessarily that every ordinary rewrite is unsafe.\nUnknown/missing/contradictory route fields, invalid or partially rejected actions/reviews, paragraph overlap, compilation failure and invalid patch remain no-op. A failed local writer, rejected candidate or safety stop NEVER gets a second ordinary writer. Each round permits one planner and at most one writer (local OR Targeted). No repair/resampling of planner/writer responses. An accepted identity/no-op is NOT a successful experience. Prior execution_summary records distinguish actual changes and ordinary fallback from history-backed local editing.\nThe schema and meaning above extend the three existing top-level fields specified below; the original action correspondence/preservation rules continue unchanged. Route choices and preservation_risk are model declarations, not safety proofs. Preserve unique claims and supplied-source boundaries on every route.\n'


def build_candidate_planner_prompt(current, sources, round_no, history, catalog):
    return (
        ROUTED_PLANNER_CONTRACT
        + "\n"
        + sm.build_planner_prompt(current, sources, round_no, history, catalog)
    )


def validate_routed_plan(raw, current, catalog, history):
    """Bind an explicit route to current feedback, never infer semantic safety.

    Top-level/schema errors raise ValueError. C2 partial rejection is retained
    in the returned plan with route_audit.valid=False, so runtime can preserve
    the evidence while keeping the whole opportunity a no-op.
    """
    _need(isinstance(raw, dict), "Routed planner response must be an object.")
    _need(set(raw) == PLAN_FIELDS | ROUTE_FIELDS, "Missing or unknown top-level route/plan fields.")
    mode = raw["route"]
    _need(mode in {"local_edit", "targeted_fallback", "stop"}, "Unknown route.")
    _need(type(raw["preservation_risk"]) is bool, "preservation_risk must be a JSON boolean.")
    reason = sm._brief(raw["route_reason"], "route_reason")
    refs = raw["fallback_evidence"]
    _need(
        isinstance(refs, list) and len(refs) <= 3,
        "fallback_evidence must contain at most three entries.",
    )
    plan = sm.validate_plan({k: raw[k] for k in PLAN_FIELDS}, current, catalog, history)
    issues = []
    if plan.get("rejected_actions") or plan.get("rejected_card_reviews"):
        issues.append("C2 rejected part of the plan; no route may bypass that rejection.")
    if mode == "local_edit":
        if not plan["actions"] or not raw["actions"]:
            issues.append("local_edit needs a nonempty valid action plan.")
        if refs:
            issues.append("local_edit cannot declare fallback evidence.")
    elif raw["actions"] or plan["actions"]:
        issues.append("Fallback and stop require empty actions.")
    if raw["preservation_risk"] and mode != "stop":
        issues.append("Declared preservation risk requires stop.")
    if mode == "stop" and refs:
        issues.append("stop cannot declare fallback evidence.")
    if mode == "targeted_fallback" and (not refs):
        issues.append("Fallback needs current locatable judge evidence.")
    bound, seen = ([], set())
    if refs:
        _need(
            len(json.dumps(refs, ensure_ascii=False)) <= 9000,
            "Fallback evidence exceeds the complete evidence budget.",
        )
        for item in refs:
            _need(
                isinstance(item, dict) and set(item) == EVIDENCE_FIELDS,
                "Missing or unknown fallback evidence fields.",
            )
            dimension, index = (item["dimension"], item["evidence_index"])
            _need(
                isinstance(dimension, str) and dimension in pipeline.JUDGE_DIMENSIONS,
                "Unknown feedback dimension.",
            )
            _need(
                type(index) is int and index >= 0,
                "evidence_index must be a nonnegative integer, not boolean.",
            )
            _need((dimension, index) not in seen, "Duplicate feedback reference.")
            seen.add((dimension, index))
            finding = current.get("judge_score", {}).get("dimensions", {}).get(dimension, {})
            _need(
                isinstance(finding, dict)
                and _finite(finding.get("score"))
                and (finding["score"] > 0),
                "Fallback evidence must belong to a positive CURRENT judge score.",
            )
            evidence = finding.get("evidence", [])
            _need(
                isinstance(evidence, list) and index < len(evidence),
                "Feedback evidence index does not exist.",
            )
            _need(
                isinstance(item["quote"], str) and item["quote"] == evidence[index],
                "Fallback quote must exactly equal the original current judge evidence.",
            )
            location = sm._bind(
                current["text"], {"section": item["section"], "quote": item["quote"]}
            )
            explanation = sm._brief(item["expression_issue"], "expression_issue")
            bound.append(
                {
                    **location,
                    "dimension": dimension,
                    "evidence_index": index,
                    "judge_dimension_score": finding["score"],
                    "expression_issue": explanation,
                }
            )
    audit = {
        "schema_version": ROUTE_VERSION,
        "requested_route": mode,
        "validated_route": mode if not issues else "invalid_noop",
        "valid": not issues,
        "issues": issues,
        "reason": reason,
        "preservation_risk_declared": raw["preservation_risk"],
        "current_text_hash": pipeline.input_hash(current["text"]),
        "current_judge_hash": pipeline.input_hash(current["judge_score"]),
        "bound_feedback": bound,
        "feedback_locator_verified": mode == "targeted_fallback" and bool(bound) and (not issues),
        "semantic_safety_proven": False,
        "note": "Exact current feedback binding and model risk declaration do not prove safe or useful rewriting.",
    }
    plan["route_audit"] = audit
    return plan


def _source_hashes():
    import hashlib

    root = Path(__file__).resolve().parent
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*.py"))
    }


def run_candidate_branch(
    store,
    initial,
    targeted_round1,
    sources,
    branch,
    *,
    frozen_catalog,
    shared_warmup_call_records=None,
    on_round=None,
    resume=False,
):
    """Run rounds 2 and 3 with explicit local/fallback/stop routing from shared R1.

    Return {versions: [shared_R1, R2, R3], final, history, manifest, cost}.
    Branch labels affect artifact names/events only, never planner/writer text.
    P/M both use the same functions and roles. Strict resume replays identical
    requests from the same store/cache; missing responses can finish once.
    """
    _need(branch in {"planner", "memory"}, "Expected planner or memory branch.")
    _need(
        isinstance(frozen_catalog, dict) and isinstance(frozen_catalog.get("cards"), list),
        "Supply the explicitly frozen C2 catalog, or its empty planner control.",
    )
    _need(
        branch != "planner" or not frozen_catalog["cards"],
        "Planner control must have an empty catalog.",
    )
    warmup, current, evidence = verify_shared_warmup(initial, targeted_round1, sources)
    sources, catalog = (deepcopy(sources), deepcopy(frozen_catalog))
    catalog_hash = pipeline.input_hash(catalog)
    directory = Path(store.directory) / ("planned_" + branch)
    _need(
        not directory.exists() or resume,
        "Candidate directory exists; explicit resume=True required.",
    )
    directory.mkdir(parents=True, exist_ok=True)
    attempt_dir = directory / "attempts" / uuid4().hex
    attempt_dir.mkdir(parents=True)
    start_calls = len(store.calls)
    versions, history = ([warmup], [])
    counts = {
        "planner_requests": 0,
        "patch_writer_requests": 0,
        "targeted_fallback_writer_requests": 0,
    }
    manifest = {
        "schema_version": VERSION,
        "candidate_not_validated": True,
        "route_contract_version": ROUTE_VERSION,
        "is_test_fixture": bool(getattr(store, "is_test_fixture", False)),
        "model": store.model,
        "branch": branch,
        "local_rounds": [2, 3],
        "catalog_hash": catalog_hash,
        "sources_hash": pipeline.input_hash(sources),
        "source_hashes": _source_hashes(),
        "shared_warmup": evidence,
        "shared_warmup_cost_supplied": shared_warmup_call_records is not None,
        "scope": "One shared Targeted first round, then two explicitly routed opportunities; at most one local or ordinary writer per slot.",
        "history_scope": "Only this branch's routed rounds 2 and 3; no warm-up or other-branch history.",
        "call_limits": {
            "planner_per_local_round": 1,
            "total_writer_per_round": 1,
            "local_or_fallback_writer_mutually_exclusive": True,
        },
        "shared_checker_repairs": "Original guard/judge may perform their existing JSON repair; these are separate recorded calls, not extra writer candidates.",
    }
    pipeline.write_json(attempt_dir / "status.json", {"status": "running", "resume": resume})
    try:
        _ensure_json(directory / "manifest.json", manifest)
        _ensure_json(directory / "sources_snapshot.json", sources)
        _ensure_json(directory / "catalog_snapshot.json", catalog)
        _ensure_json(directory / "initial_record.json", initial)
        _ensure_json(directory / "shared_targeted_round1_original.json", targeted_round1)
        _ensure_json(directory / "shared_warmup_verification.json", evidence)
        _ensure_json(directory / "shared_warmup_call_records.json", shared_warmup_call_records)
        _ensure_json(directory / "round_1.json", warmup)
        _ensure_bytes(directory / "round_1_selected.md", current["text"].encode("utf-8"))
        for round_number in (2, 3):
            _need(
                pipeline.input_hash(catalog) == catalog_hash,
                "Frozen catalog changed inside the run.",
            )
            round_dir = directory / f"round_{round_number}"
            round_dir.mkdir(exist_ok=True)
            previous = deepcopy(current)
            history_before = deepcopy(history)
            store.status(
                f"{branch}_local_round_{round_number}",
                message=f"Explicitly routed candidate, round {round_number}/3.",
            )
            planner_agent = f"semantic_planner_round_{round_number}"
            writer_agent = f"semantic_patch_writer_round_{round_number}"
            planner_prompt = build_candidate_planner_prompt(
                current, sources, round_number, history, catalog
            )
            _ensure_bytes(round_dir / "planner_request.txt", planner_prompt.encode("utf-8"))
            stage_start = len(store.calls)
            counts["planner_requests"] += 1
            raw_plan = _ask_once(
                store,
                planner_agent,
                planner_prompt,
                round_dir / "planner_response.txt",
                attempt_dir,
            )
            _need(isinstance(raw_plan, str), "Planner must return its raw text response.")
            plan, reasons, execution_valid, execution_admitted = (None, [], False, False)
            writer_prompt, raw_patch, patch_result, writer_calls = (None, None, None, [])
            fallback_text = None
            execution_mode = "invalid_noop"
            parsed_plan = None
            try:
                parsed_plan = pipeline.parse_json_response(raw_plan)
                plan = validate_routed_plan(parsed_plan, current, catalog, history)
                _need(plan["route_audit"]["valid"], "; ".join(plan["route_audit"]["issues"]))
                execution_mode = plan["route_audit"]["validated_route"]
                execution_valid = True
            except (ValueError, TypeError, KeyError) as error:
                reasons.append("invalid_plan: " + str(error))
            _ensure_json(round_dir / "validated_plan.json", plan)
            if execution_valid and execution_mode == "stop":
                reasons.append("explicit_stop: " + plan["route_audit"]["reason"])
            elif execution_valid and execution_mode == "targeted_fallback":
                fallback_dir = round_dir / "targeted_fallback"
                fallback_dir.mkdir(exist_ok=True)
                writer_agent = f"targeted_rewriter_round_{round_number}"
                writer_prompt = targeted_prompt(current, sources)
                _ensure_bytes(fallback_dir / "writer_request.txt", writer_prompt.encode("utf-8"))
                stage_start = len(store.calls)
                counts["targeted_fallback_writer_requests"] += 1
                raw_patch = _ask_once(
                    store,
                    writer_agent,
                    writer_prompt,
                    fallback_dir / "writer_response.txt",
                    attempt_dir,
                )
                writer_calls = deepcopy(store.calls[stage_start:])
                try:
                    fallback_text = pipeline.normalize_six_sections(raw_patch)
                    normalization = "original_targeted_section_normalization"
                except ValueError:
                    fallback_text = raw_patch
                    normalization = (
                        "raw_response_after_normalization_error_shared_guard_still_required"
                    )
                execution_admitted = True
                _ensure_bytes(fallback_dir / "candidate.md", fallback_text.encode("utf-8"))
                _ensure_json(
                    fallback_dir / "execution_result.json",
                    {
                        "schema_version": VERSION,
                        "route_admitted": True,
                        "route": execution_mode,
                        "text": fallback_text,
                        "normalization": normalization,
                        "original_text_hash": current["text_hash"],
                        "candidate_text_hash": pipeline.input_hash(fallback_text),
                        "writer_agent": writer_agent,
                        "writer_prompt_hash": pipeline.input_hash(writer_prompt),
                        "historical_card_ids": [],
                        "memory_credit": False,
                        "semantic_safety_proven": False,
                    },
                )
            elif execution_valid and execution_mode == "local_edit":
                prepared = _prepare_patch_checkpoint(
                    round_dir / "patch_attempt",
                    attempt_dir / f"compiled_round_{round_number}",
                    current["text"],
                    plan,
                    sources,
                    catalog,
                    {"rule_score": current["rule_score"], "judge_score": current["judge_score"]},
                    planner_prompt,
                    raw_plan,
                )
                if not prepared["writer_call_allowed"]:
                    execution_valid = False
                    reasons.extend(
                        ("compile_failure: " + issue for issue in prepared.get("issues", []))
                    )
                else:
                    writer_prompt = prepared["writer_request"]
                    stage_start = len(store.calls)
                    counts["patch_writer_requests"] += 1
                    raw_patch = _ask_once(
                        store,
                        writer_agent,
                        writer_prompt,
                        round_dir / "patch_attempt/writer_response.txt",
                        attempt_dir,
                    )
                    writer_calls = deepcopy(store.calls[stage_start:])
                    contract = executor.compile_edit_contract(current["text"], plan, catalog)
                    patch_result = executor.apply_patch_response(
                        current["text"], contract, raw_patch
                    )
                    _ensure_json(round_dir / "patch_attempt/execution_result.json", patch_result)
                    _ensure_bytes(
                        round_dir / "patch_attempt/candidate.md",
                        patch_result["text"].encode("utf-8"),
                    )
                    execution_valid = patch_result["valid"]
                    execution_admitted = execution_valid
                    if not execution_valid:
                        reasons.extend(
                            ("invalid_patch: " + issue for issue in patch_result["issues"])
                        )
            if not execution_valid:
                execution_mode = "invalid_noop"
            candidate_text = (
                fallback_text
                if fallback_text is not None
                else patch_result["text"] if patch_result is not None else current["text"]
            )
            if candidate_text == current["text"] and (not reasons):
                reasons.append(
                    "valid_writer_no_change: writer returned the original text or paragraphs"
                )
            evaluated_path = round_dir / "shared_evaluation_checkpoint.json"
            if evaluated_path.exists():
                checkpoint = json.loads(evaluated_path.read_bytes())
                for call in checkpoint["calls"]:
                    _cache_record(store, call["input_hash"])
            stage_start = len(store.calls)
            guard = revision_verifier.check_content_preservation(
                store, current["text"], candidate_text, sources
            )
            candidate = pipeline.evaluate_version(store, candidate_text, round_number, sources)
            if candidate_text == current["text"]:
                _need(
                    candidate["score"] == current["score"]
                    and candidate["rule_score"] == current["rule_score"]
                    and (candidate["judge_score"] == current["judge_score"]),
                    "Identity no-op was rescored differently; reuse/import its original judge cache instead of resampling.",
                )
            selector_accepted, selected = pipeline.select_candidate(current, candidate, guard)
            evaluation_calls = deepcopy(store.calls[stage_start:])
            pipeline.write_json(
                attempt_dir / f"round_{round_number}_evaluation_calls.json", evaluation_calls
            )
            _ensure_json(
                evaluated_path,
                {
                    "candidate": candidate,
                    "guard": guard,
                    "calls": _call_identities(evaluation_calls),
                },
            )
            changed = candidate_text != current["text"]
            observed_accepted_change = bool(execution_admitted and changed and selector_accepted)
            sent_cards = (
                sorted(
                    {
                        card
                        for action in (plan or {}).get("actions", [])
                        for card in action["memory_card_ids"]
                    }
                )
                if writer_prompt
                and (plan or {}).get("route_audit", {}).get("validated_route") == "local_edit"
                else []
            )
            changed_action_ids = sorted(
                {
                    edit["action_id"]
                    for edit in (patch_result or {}).get("applied_edits", [])
                    if edit["changed"]
                }
            )
            historical_changed_actions = [
                a["id"]
                for a in (plan or {}).get("actions", [])
                if a["memory_card_ids"] and a["id"] in changed_action_ids
            ]
            decision = (
                "no_op"
                if not changed
                else "accepted_edit" if selector_accepted else "rejected_edit"
            )
            injection = {
                "writer_request_sent": writer_prompt is not None,
                "card_ids_sent": sent_cards,
                "coverage_eligible": bool(sent_cards and writer_prompt),
                "changed_historical_action_ids": historical_changed_actions,
                "actual_operation_execution_requires_review": bool(historical_changed_actions),
                "counts_as_success_experience": False,
                "note": "Sent history is not executed history. Changed authorized scope is not proof of the intended operation or its causal benefit. No online library updates.",
            }
            round_audit = {
                "round": round_number,
                "sources_hash": manifest["sources_hash"],
                "catalog_hash": catalog_hash,
                "current_text_hash": current["text_hash"],
                "history_before": history_before,
                "plan": plan,
                "planner_request_hash": pipeline.input_hash(planner_prompt),
                "planner_response_raw_sha256": executor.sha256(raw_plan),
                "writer_request_hash": (
                    pipeline.input_hash(writer_prompt) if writer_prompt else None
                ),
                "writer_response_raw_sha256": (
                    executor.sha256(raw_patch) if raw_patch is not None else None
                ),
                "execution_valid": execution_valid,
                "execution_admitted": execution_admitted,
                "decision_kind": decision,
                "no_op_reasons": reasons,
                "history_injection": injection,
                "writer_call_identities": _call_identities(writer_calls),
                "evaluation_call_identities": _call_identities(evaluation_calls),
                "requested_route": (
                    parsed_plan.get("route") if isinstance(parsed_plan, dict) else None
                ),
                "route_validation": (plan or {}).get("route_audit"),
                "effective_execution_mode": execution_mode,
                "full_manuscript_fallback": execution_mode == "targeted_fallback",
                "fallback_memory_credit": False,
                "resampled": False,
            }
            candidate.update(
                accepted=selector_accepted,
                selector_accepted=selector_accepted,
                guard=guard,
                branch=branch,
                execution_valid=execution_valid,
                execution_admitted=execution_admitted,
                decision_kind=decision,
                no_op_reasons=reasons,
                changed=changed,
                observed_accepted_change=observed_accepted_change,
                original_text=current["text"],
                previous_text_hash=current["text_hash"],
                selected_score=deepcopy(selected["score"]),
                selected_text_hash=selected["text_hash"],
                effective_generator_agent=writer_agent if writer_prompt else None,
                prompt_has_retrieved_memory=bool(sent_cards),
                prompt_has_transfer_memory=bool(sent_cards),
                prompt_has_examples=bool(sent_cards),
                prompt_has_local_memory=False,
                historical_card_ids_sent_to_writer=sent_cards,
                memory_credit=False,
                local_runtime_audit=round_audit,
                routed_execution_mode=execution_mode,
                full_manuscript_fallback=execution_mode == "targeted_fallback",
                diff="\n".join(
                    difflib.unified_diff(
                        current["text"].splitlines(),
                        candidate_text.splitlines(),
                        fromfile="previous",
                        tofile="candidate",
                        lineterm="",
                    )
                ),
            )
            outcome = _history_record(
                round_number, plan or {"actions": []}, previous, candidate, selected
            )
            outcome.update(
                accepted=selector_accepted,
                selector_accepted=selector_accepted,
                execution_valid=execution_valid,
                execution_admitted=execution_admitted,
                changed=changed,
                decision_kind=decision,
                no_op_reasons=reasons,
                observed_accepted_change=observed_accepted_change,
                interpretation="Accepted preserves the unmodified shared selector, including identity no-ops. Only observed_accepted_change denotes an actual accepted edit; none proves causal benefit.",
            )
            outcome["target_observations"].append(
                {
                    "kind": "execution_summary",
                    "decision_kind": decision,
                    "execution_valid": execution_valid,
                    "execution_admitted": execution_admitted,
                    "changed": changed,
                    "selector_accepted": selector_accepted,
                    "no_op_reasons": reasons,
                    "observed_accepted_change": observed_accepted_change,
                    "counts_as_success_experience": False,
                    "route": execution_mode,
                    "route_reason": (plan or {}).get("route_audit", {}).get("reason"),
                    "full_manuscript_fallback": execution_mode == "targeted_fallback",
                    "memory_credit": False,
                    "note": "An identity candidate can pass the shared selector without an accepted edit or successful experience.",
                }
            )
            history.append(outcome)
            candidate["semantic_outcome"] = outcome
            versions.append(candidate)
            current = deepcopy(selected)
            _ensure_json(round_dir / "runtime_audit.json", round_audit)
            _ensure_json(directory / f"round_{round_number}.json", candidate)
            _ensure_json(directory / f"history_after_round_{round_number}.json", history)
            _ensure_bytes(
                directory / f"round_{round_number}_candidate.md", candidate_text.encode("utf-8")
            )
            _ensure_bytes(
                directory / f"round_{round_number}_selected.md", current["text"].encode("utf-8")
            )
            store.event(
                "revision_round_completed",
                branch=branch,
                round=round_number,
                selector_accepted=selector_accepted,
                decision_kind=decision,
                changed=changed,
                execution_valid=execution_valid,
                card_ids_sent=sent_cards,
            )
            if on_round:
                on_round(deepcopy(versions), deepcopy(current))
    except Exception as error:
        _record_failure(attempt_dir, error, resume, store.calls[start_calls:], counts)
        raise
    post_calls = deepcopy(store.calls[start_calls:])
    cost = {
        "scope": "Current invocation only; retain and aggregate earlier attempt records for physical spending.",
        "post_warmup": _cost(post_calls),
        "logical_request_counts": counts,
        "post_warmup_call_records": post_calls,
        "shared_warmup_call_records": deepcopy(shared_warmup_call_records),
        "shared_warmup_cost_known": shared_warmup_call_records is not None,
        "full_method_logical_records": (
            deepcopy(shared_warmup_call_records) + post_calls
            if shared_warmup_call_records is not None
            else None
        ),
        "comparison_note": "P/M have identical planning/writer opportunities, not identical token usage; both incur up to two planner requests beyond original three-round Targeted. Shared R1 costs belong in every complete method's logical cost, but only once in physical spending.",
    }
    manifest = {**manifest, "status": "completed", "final_text_hash": current["text_hash"]}
    result = {
        "schema_version": VERSION,
        "branch": branch,
        "versions": versions,
        "final": current,
        "history": history,
        "manifest": manifest,
        "output_dir": directory.name,
    }
    try:
        _ensure_json(directory / "branch_local_history.json", history)
        _ensure_json(directory / "result.json", result)
    except Exception as error:
        _record_failure(attempt_dir, error, resume, post_calls, counts)
        raise
    pipeline.write_json(attempt_dir / "status.json", {"status": "completed", "resume": resume})
    pipeline.write_json(attempt_dir / "completed_call_records.json", post_calls)
    pipeline.write_json(attempt_dir / "cost.json", cost)
    return {**result, "cost": cost, "attempt_dir": str(attempt_dir)}
