from copy import deepcopy
import json, math
from pathlib import Path
from . import pipeline, local_executor as executor
from .revision_prompts import targeted_prompt


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _finite(value):
    return (
        isinstance(value, (int, float)) and (not isinstance(value, bool)) and math.isfinite(value)
    )


def _validate_version(version, label):
    _need(
        isinstance(version, dict)
        and isinstance(version.get("text"), str)
        and version["text"].strip(),
        label + " requires a scored manuscript record.",
    )
    _need(
        version.get("text_hash") == pipeline.input_hash(version["text"]),
        label + " text hash mismatch.",
    )
    score = version.get("score", {}).get("score")
    rule = version.get("rule_score", {}).get("score")
    judge = version.get("judge_score", {}).get("score")
    _need(
        all((_finite(v) for v in (score, rule, judge))), label + " has missing/non-finite scores."
    )
    _need(
        score == round(0.3 * rule + 0.7 * judge, 3),
        label + " does not use the unchanged shared score.",
    )


def verify_shared_warmup(initial, targeted_round1, sources):
    """Verify lineage and recompute selection, never choose from later T drafts.

    This checks supplied records, not provider authenticity or score truth.
    Actual warm-up requests/responses and costs remain the caller's provenance.
    """
    _validate_version(initial, "Initial")
    _validate_version(targeted_round1, "Targeted round 1")
    _need(type(initial.get("round")) is int and initial["round"] == 0, "Initial must be round 0.")
    _need(
        type(targeted_round1.get("round")) is int and targeted_round1["round"] == 1,
        "Only the actual Targeted first round is allowed; later/best drafts are forbidden.",
    )
    _need(
        targeted_round1.get("branch") == "targeted"
        and targeted_round1.get("effective_generator_agent") == "targeted_rewriter_round_1",
        "Warm-up must identify the original Targeted first-round generator.",
    )
    _need(
        targeted_round1.get("previous_text_hash") == initial["text_hash"]
        and targeted_round1.get("original_text") == initial["text"],
        "Warm-up does not descend directly from the supplied initial manuscript.",
    )
    guard = targeted_round1.get("guard")
    _need(
        isinstance(guard, dict) and type(guard.get("passed")) is bool,
        "Warm-up needs its original guard.",
    )
    accepted, selected = pipeline.select_candidate(initial, targeted_round1, guard)
    _need(
        type(targeted_round1.get("accepted")) is bool and targeted_round1["accepted"] == accepted,
        "Stored warm-up decision disagrees with original select_candidate.",
    )
    _need(
        targeted_round1.get("selected_text_hash") == selected["text_hash"]
        and targeted_round1.get("selected_score") == selected["score"],
        "Stored warm-up retained state disagrees with original select_candidate.",
    )
    record = deepcopy(targeted_round1)
    record.update(
        branch="shared_targeted_warmup",
        original_branch="targeted",
        selector_accepted=accepted,
        decision_kind="shared_targeted_warmup",
        memory_credit=False,
        prompt_has_retrieved_memory=False,
        prompt_has_transfer_memory=False,
        prompt_has_examples=False,
        historical_card_ids_sent_to_writer=[],
        selected_text_hash=selected["text_hash"],
        selected_score=deepcopy(selected["score"]),
    )
    evidence = {
        "initial_record_hash": pipeline.input_hash(initial),
        "targeted_round1_record_hash": pipeline.input_hash(targeted_round1),
        "sources_hash": pipeline.input_hash(sources),
        "first_round_candidate_hash": targeted_round1["text_hash"],
        "retained_text_hash": selected["text_hash"],
        "retained_raw_utf8_sha256": executor.sha256(selected["text"]),
        "recomputed_selector_accepted": accepted,
        "memory_credit": False,
        "expected_original_targeted_request_hash": pipeline.input_hash(
            targeted_prompt(initial, sources)
        ),
        "record_lineage_verified": True,
        "provider_authenticity_verified": False,
        "note": "Expected prompt is derived, not evidence of an observed provider request. Preserve original warm-up trace separately.",
    }
    return (record, deepcopy(selected), evidence)


def _ensure_bytes(path, raw):
    """Immutable checkpoint: conflict is an error, never an overwrite."""
    path = Path(path)
    if path.exists():
        _need(path.read_bytes() == raw, "Resume conflict: " + str(path))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as output:
            output.write(raw)


def _ensure_json(path, value):
    _ensure_bytes(path, (executor._json(value) + "\n").encode("utf-8"))


def _call_identities(records):
    return [{"agent": c["agent"], "input_hash": c["input_hash"]} for c in records]


def _cache_record(store, digest):
    _need(hasattr(store, "cache"), "Resume requires the original CallStore-compatible cache.")
    path = Path(store.cache) / (digest + ".json")
    _need(
        path.is_file(), "Completed response has no original cache; refusing a new sample: " + digest
    )
    record = json.loads(path.read_bytes())
    _need(
        record.get("input_hash") == digest and pipeline.input_hash(record.get("request")) == digest,
        "Cache provenance conflict: " + digest,
    )
    return record


def _ask_once(store, name, prompt, response_path, audit_dir):
    """At most one store request; an existing response MUST come from cache."""
    request = {
        "version": pipeline.VERSION,
        "agent": name,
        "model": store.model,
        "messages": [{"role": "human", "content": prompt}],
    }
    digest = pipeline.input_hash(request)
    _ensure_json(
        response_path.with_name(response_path.stem + "_request_record.json"),
        {"input_hash": digest, "request": request},
    )
    if response_path.exists():
        cached = _cache_record(store, digest)
        _need(cached["request"] == request, "Stored request and cache disagree.")
        _need(
            cached["response"].get("content") == response_path.read_bytes().decode("utf-8"),
            "Completed response differs from its cache; refusing a new sample.",
        )
    start = len(store.calls)
    try:
        raw = store.ask(name, prompt)
        _need(isinstance(raw, str), "Store must return raw text.")
        _ensure_bytes(response_path, raw.encode("utf-8"))
        return raw
    finally:
        pipeline.write_json(audit_dir / (name + "_calls.json"), store.calls[start:])


def _prepare_patch_checkpoint(
    directory,
    verification_dir,
    text,
    plan,
    sources,
    catalog,
    feedback,
    planner_request,
    planner_response,
):
    """Recompute with the executor itself, then validate/fill immutable artifacts."""
    prepared = executor.prepare_attempt(
        verification_dir,
        text,
        plan,
        sources,
        catalog=catalog,
        feedback=feedback,
        planner_request=planner_request,
        planner_response=planner_response,
    )
    files = [
        (directory / p.relative_to(verification_dir), p.read_bytes())
        for p in verification_dir.rglob("*")
        if p.is_file()
    ]
    for path, raw in files:
        if path.exists():
            _need(path.read_bytes() == raw, "Resume compiler conflict: " + str(path))
    for path, raw in files:
        _ensure_bytes(path, raw)
    return prepared


def _cost(records):
    tokens, unknown, cache_hits = (0, 0, 0)
    for record in records:
        if record.get("cached") is True:
            cache_hits += 1
            continue
        usage = record.get("usage", {})
        total = usage.get("total_tokens") if isinstance(usage, dict) else None
        if not _finite(total) or total < 0:
            unknown += 1
        else:
            tokens += total
    return {
        "completed_records": len(records),
        "cache_hit_records": cache_hits,
        "noncached_completed_records": len(records) - cache_hits,
        "reported_noncached_total_tokens": tokens,
        "completed_unknown_usage_records": unknown,
        "note": "Transport failures and missing usage are not free. Store/provider accounting remains authoritative.",
    }


def _record_failure(attempt_dir, error, resume, records, counts):
    pipeline.write_json(
        attempt_dir / "status.json",
        {
            "status": "failed",
            "error_type": type(error).__name__,
            "error": str(error),
            "resume": resume,
            "note": "No automatic retry/resampling. All prior artifacts remain; failed request usage can be unknown.",
        },
    )
    pipeline.write_json(attempt_dir / "completed_call_records.json", records)
    pipeline.write_json(attempt_dir / "logical_request_counts.json", counts)
