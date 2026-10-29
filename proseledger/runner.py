"""One product, one callable workflow, three explicitly compared revision methods."""

from contextlib import contextmanager
from copy import deepcopy
import hashlib, json, os
from pathlib import Path
from . import pipeline
from .draft_workflow import generate_draft
from .targeted import run_targeted
from .revision_controller import run_candidate_branch
from .preservation import check_content_preservation

DATA = Path(__file__).resolve().parents[1] / "data"
METHODS = ("targeted", "planner", "memory")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def output_text(path, text):
    Path(path).write_text(text, encoding="utf-8", newline="\n")


def verify_resources():
    manifest = read(DATA / "integrity.json")
    for name, digest in manifest["files"].items():
        path = (DATA / name).resolve()
        if not path.is_relative_to(DATA.resolve()) or not path.is_file() or sha(path) != digest:
            raise ValueError("Bundled runtime resource differs: " + name)
    return manifest


def source_fingerprint():
    root = Path(__file__).resolve().parent
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob("*.py"))}


def verify_runtime():
    """Check frozen inputs and import the drafting graph without model calls."""
    from .drafting.builder import build_research_workflow

    resource = verify_resources()
    sources = pipeline.load_sources(DATA / "sources.json")
    catalogs = read(DATA / "catalogs.json")
    if catalogs["planner"]["cards"]:
        raise ValueError("Planner-only must not receive historical cards.")
    if not catalogs["memory"]["cards"]:
        raise ValueError("The Memory catalog is empty.")
    return {
        "status": "passed",
        "runtime_files": len(source_fingerprint()),
        "resource_files": len(resource["files"]),
        "source_count": len(sources),
        "memory_cards": len(catalogs["memory"]["cards"]),
        "new_model_calls": 0,
        "note": "Resource validation and graph imports only; no credentials or model calls.",
    }


def cache_inventory(folder):
    result = {}
    for stage in ("draft_stage", "revision_stage"):
        for path in sorted((folder / stage / "call_cache").glob("*.json")):
            value = read(path)
            if (
                value.get("input_hash") != path.stem
                or pipeline.input_hash(value.get("request")) != path.stem
            ):
                raise ValueError("Invalid cached request identity: " + path.name)
            result[path.relative_to(folder).as_posix()] = sha(path)
    return result


def verify_previous_cache(folder):
    checkpoint = folder / "cache_integrity.json"
    if not checkpoint.exists():
        return
    for name, digest in read(checkpoint)["files"].items():
        path = folder / name
        if not path.is_file() or sha(path) != digest:
            raise ValueError("A previously completed model response changed: " + name)


@contextmanager
def execution_lock(folder):
    path = folder.parent / ("." + folder.name + ".lock")
    with path.open("a+b") as f:
        try:
            if os.name == "nt":
                import msvcrt

                if os.fstat(f.fileno()).st_size == 0:
                    f.write(b"0")
                    f.flush()
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise RuntimeError("This run is already executing.") from error
        try:
            yield
        finally:
            if os.name == "nt":
                f.seek(0)
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


class ProductStore(pipeline.CallStore):
    """Write status and events at both the stage and the run level."""

    def __init__(self, directory, *, output, **kwargs):
        directory.mkdir(parents=True, exist_ok=True)
        super().__init__(directory, **kwargs)
        self.output = output

    def status(self, stage, status="running", message=""):
        super().status(stage, status, message)
        pipeline.write_json(
            self.output / "status.json",
            {
                "stage": stage,
                "status": status,
                "message": message,
                "updated_at": pipeline.utc_now(),
            },
        )

    def event(self, kind, **values):
        super().event(kind, **values)
        with (self.output / "events.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(
                json.dumps(
                    {"time": pipeline.utc_now(), "stage": self.stage, "event": kind, **values},
                    ensure_ascii=False,
                )
                + "\n"
            )


def final_check(store, initial, final, sources):
    guard = check_content_preservation(store, initial, final, sources, phase="final")
    return {
        "status": "completed",
        "model_audit": guard["semantic_audit"],
        "adjudicated_guard": guard,
        "failure_flag": not guard["passed"],
        "identity_verified": initial == final,
        "note": "Automated concern flag, not human truth.",
    }


def row_from_candidate(c):
    audit = c.get("local_runtime_audit", {})
    return {
        "round": c["round"],
        "candidate_score": c["score"]["score"],
        "retained_score": c["selected_score"]["score"],
        "accepted": c["accepted"],
        "changed": c.get("changed", False),
        "guard_passed": c["guard"]["passed"],
        "route": c.get(
            "routed_execution_mode",
            (
                "shared_first_round"
                if c.get("shared_warmup") or c.get("memory_credit") is False and c["round"] == 1
                else "targeted"
            ),
        ),
        "memory_used": bool(c.get("historical_card_ids_sent_to_writer")),
        "memory_card_ids": c.get("historical_card_ids_sent_to_writer", []),
        "decision": c.get(
            "decision_kind",
            (
                "accepted_edit"
                if c["accepted"] and c.get("changed")
                else "rejected_edit" if not c["accepted"] else "no_op"
            ),
        ),
    }


def make_summary(folder, result, stores, mode):
    branches = {}
    for method in METHODS:
        data = result[method]
        final = data["final"]
        filename = f"proposal_{method}.md"
        output_text(folder / filename, final["text"])
        branches[method] = {
            "final_score": final["score"]["score"],
            "final_text_path": filename,
            "text_sha256": hashlib.sha256(final["text"].encode("utf-8")).hexdigest(),
            "rounds": [row_from_candidate(c) for c in data["versions"]],
            "final_preservation": result["fidelity"][method]["model_audit"]["verdict"],
        }
    all_calls = [c for store in stores for c in store.calls]
    new = sum(not c.get("cached", False) for c in all_calls)
    return {
        "status": "completed",
        "mode": mode,
        "schema": "proseledger-product-1",
        "model": stores[0].model,
        "input": {
            "topic": result["topic"],
            "sources_count": len(result["sources"]),
            "source_titles": [s["title"] for s in result["sources"]],
        },
        "initial_score": result["initial"]["score"]["score"],
        "initial_text_path": "proposal_initial.md",
        "branches": branches,
        "comparison": {
            "memory_minus_targeted": round(
                branches["memory"]["final_score"] - branches["targeted"]["final_score"], 3
            ),
            "memory_minus_planner": round(
                branches["memory"]["final_score"] - branches["planner"]["final_score"], 3
            ),
        },
        "new_model_calls": new,
        "cached_call_records": sum(bool(c.get("cached")) for c in all_calls),
        "score_description": "30% transparent style rules + 70% fixed model rubric. Lower is better; not an authorship probability.",
        "scope": "One fresh generation; separate from the archived six-manuscript evaluation.",
        "display_method": "memory",
        "display_policy": "Always export the Memory retained proposal; never choose the winning branch for display.",
        "completed_at": pipeline.utc_now(),
    }


def execute(
    output,
    *,
    sources_path=None,
    topic=None,
    mode="live",
    resume=False,
    model="gpt-6.1-sol",
    timeout=240,
):
    folder = Path(output).resolve()
    folder.parent.mkdir(parents=True, exist_ok=True)
    if model != "gpt-6.1-sol":
        raise ValueError("The comparison protocol fixes the model to gpt-6.1-sol.")
    if mode != "live":
        raise ValueError(
            "This source release supports fresh generation only. Read saved evaluation records in docs/index.html."
        )
    verify_resources()
    if not sources_path or not topic or not topic.strip():
        raise ValueError("Provide a source JSON and a nonempty topic.")
    sources = pipeline.load_sources(sources_path)
    catalogs = read(DATA / "catalogs.json")
    contract = {
        "mode": mode,
        "model": model,
        "topic": topic,
        "sources": sources,
        "rounds": 3,
        "runtime_sha256": source_fingerprint(),
        "catalog_sha256": sha(DATA / "catalogs.json"),
        "schema": "proseledger-product-1",
    }
    with execution_lock(folder):
        if (folder / "manifest.json").exists():
            if not resume or read(folder / "manifest.json")["contract"] != contract:
                raise ValueError(
                    "Run already exists or configuration changed. Resume unchanged input, or choose a new output folder."
                )
            verify_previous_cache(folder)
        elif folder.exists() and any(folder.iterdir()):
            raise ValueError("Output folder must be empty for a new run.")
        else:
            folder.mkdir(parents=True, exist_ok=True)
            pipeline.write_json(
                folder / "manifest.json",
                {
                    "contract": contract,
                    "contract_hash": pipeline.input_hash(contract),
                    "started_at": pipeline.utc_now(),
                },
            )
        pipeline.write_json(folder / "sources.json", sources)
        pipeline.write_json(folder / "catalogs.json", catalogs)
        stores = []
        try:
            for stage in ["draft_stage", "revision_stage"]:
                dest = folder / stage / "call_cache"
                dest.mkdir(parents=True, exist_ok=True)
                stores.append(
                    ProductStore(folder / stage, output=folder, model=model, timeout=timeout)
                )
            draft_store, store = stores
            ideas = pipeline.create_ideas(draft_store, topic, sources)
            idea = ideas[0]
            pipeline.write_json(
                folder / "ideas.json",
                {
                    "ideas": ideas,
                    "selected_id": idea["id"],
                    "selection": "Fixed first idea; no score-based idea selection.",
                },
            )
            draft, trace = generate_draft(draft_store, topic, idea, sources)
            output_text(folder / "proposal_initial.md", draft)
            pipeline.write_json(folder / "draft_trace.json", trace)
            store.status(
                "initial_evaluation",
                message="Assessing the initial proposal with the shared fixed rubric.",
            )
            initial = pipeline.evaluate_version(store, draft, 0, sources)
            pipeline.write_json(folder / "revision_stage/initial.json", initial)
            result = {"topic": topic, "sources": sources, "initial": initial, "fidelity": {}}
            warmup_calls = []

            def targeted_progress(versions, selected):
                nonlocal warmup_calls
                if len(versions) == 1:
                    observed = deepcopy(store.calls)
                    for call in observed:
                        call["cache_file"] = "call_cache/" + call["input_hash"] + ".json"
                    path = folder / "revision_stage/shared_warmup_calls.json"
                    if path.exists():
                        saved = read(path)
                        identities = lambda rows: [(r["agent"], r["input_hash"]) for r in rows]
                        if identities(saved) != identities(observed):
                            raise ValueError("Shared first-round requests changed on resume.")
                        warmup_calls = saved
                    else:
                        warmup_calls = observed
                        pipeline.write_json(path, warmup_calls)

            targeted = run_targeted(store, initial, sources, targeted_progress)
            result["targeted"] = targeted
            pipeline.write_json(folder / "revision_stage/targeted_results.json", targeted)
            for method in ["planner", "memory"]:
                result[method] = run_candidate_branch(
                    store,
                    initial,
                    deepcopy(targeted["versions"][0]),
                    sources,
                    method,
                    frozen_catalog=deepcopy(catalogs[method]),
                    shared_warmup_call_records=deepcopy(warmup_calls),
                    resume=(folder / "revision_stage" / ("planned_" + method)).exists(),
                )
                pipeline.write_json(
                    folder / "revision_stage" / f"{method}_results.json", result[method]
                )
            store.status(
                "final_content_checks",
                message="Checking every retained proposal against the initial content.",
            )
            for method in METHODS:
                result["fidelity"][method] = final_check(
                    store, draft, result[method]["final"]["text"], sources
                )
            pipeline.write_json(folder / "results.json", result)
            summary = make_summary(folder, result, stores, mode)
            output_text(
                folder / "proposal_memory_with_references.md",
                result["memory"]["final"]["text"]
                + "\n\n## References\n\n"
                + "\n".join(f"[{s['citation_key']}] {s['title']}. {s['url']}" for s in sources)
                + "\n",
            )
            pipeline.write_json(folder / "summary.json", summary)
            store.status(
                "completed",
                status="completed",
                message="New proposal generated. All branch outputs and decisions are saved.",
            )
            return summary
        except Exception as error:
            pipeline.write_json(
                folder / "status.json",
                {
                    "status": "failed",
                    "stage": "interrupted",
                    "message": str(error),
                    "error_type": type(error).__name__,
                    "updated_at": pipeline.utc_now(),
                },
            )
            raise
        finally:
            pipeline.write_json(
                folder / "cache_integrity.json",
                {
                    "files": cache_inventory(folder),
                    "scope": "Completed request-response files. Existing committed files cannot change on resume.",
                },
            )
