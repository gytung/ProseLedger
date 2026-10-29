from .pipeline import *
import json


def generate_draft(store, topic, idea, sources, *, reference_graph_id=None):
    from proseledger.drafting.base_agent import BaseAgent
    from proseledger.drafting.builder import build_research_workflow
    from proseledger.drafting.utils.constants import BEGIN_PROMPT

    code = {
        p.relative_to(ROOT).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted((ROOT / "drafting").rglob("*.py"))
    }
    graph_input = reference_graph_id or input_hash(
        {"sources": sources, "idea": idea, "topic": topic, "model": store.model, "code": code}
    )
    complete_path = store.directory / "draft_complete.json"
    if complete_path.exists() and reference_graph_id is None:
        saved = json.loads(complete_path.read_text(encoding="utf-8"))
        if saved.get("input_hash") == graph_input:
            store.event("draft_graph_cache_hit", input_hash=graph_input)
            return saved["draft"], saved["trace"]
    store.status(
        "drafting", message="Running the researcher → outline → writer → reviewer → editor graph."
    )
    run_id = graph_input[:16]
    original_factory = BaseAgent.__dict__.get("model_factory")
    BaseAgent.model_factory = staticmethod(
        lambda name, model_name, temperature: CachedAgentModel(store, name)
    )
    trace = {
        "workflow": "proseledger.drafting.builder.build_research_workflow",
        "proposal_mode": True,
        "is_mock": bool(store.model_factory),
        "input_hash": graph_input,
        "events": [],
        "terminal_reached": False,
    }
    selected_topic = (
        topic + "\nSELECTED UNVERIFIED PROPOSAL:\n" + json.dumps(idea, ensure_ascii=False)
    )
    try:
        app = build_research_workflow(
            sources,
            selected_topic,
            run_id,
            researcher_model="codex-default",
            writer_model="codex-default",
            reviewer_model="codex-default",
            editor_model="codex-default",
            max_revisions=1,
            dataset="project3",
            temp_dir=str(store.directory / "agent_records" / graph_input),
            group_size=10,
            n_jobs=1,
            n_sections=5,
            n_subsections=0,
            section_len=230,
            context_sizes={"gpt": 32000, "other": 32000},
            fulltext=False,
            setting_name="proposal",
            overwrite_responses=True,
            proposal_mode=True,
        )
        config = {"configurable": {"thread_id": run_id}, "recursion_limit": 100}
        for state in app.stream(
            {"messages": [BEGIN_PROMPT.format(REVIEW_ID=run_id)]}, config, stream_mode="values"
        ):
            progress = {
                "component": state.get("to_review_now", "research"),
                "outline_passes": state.get("revision_count_outline", 0),
                "writing_passes": state.get("revision_count_writing", 0),
                "editing_passes": state.get("revision_count_editing", 0),
            }
            trace["events"].append(progress)
            store.event("draft_graph_step", **progress)
            trace["calls"] = list(store.calls)
            write_json(store.directory / "draft_trace.json", trace)
        snapshot = app.get_state(config)
        state = snapshot.values
        if snapshot.next or not state.get("final_review"):
            raise RuntimeError("Drafting graph did not reach the final edited state.")
        draft = map_citations(normalize_six_sections(state["final_review"]), sources)
        check = proposal_checks(draft)
        if not check["passed"]:
            raise ValueError("Initial proposal failed checks: " + "; ".join(check["issues"]))
        trace.update(
            terminal_reached=True,
            draft_before_editor=state.get("draft_review", ""),
            raw_edited=state["final_review"],
            passes={
                "outline": state["revision_count_outline"],
                "writing": state["revision_count_writing"],
                "editing": state["revision_count_editing"],
            },
        )
        write_json(complete_path, {"input_hash": graph_input, "draft": draft, "trace": trace})
        return draft, trace
    finally:
        BaseAgent.model_factory = original_factory
        trace["calls"] = list(store.calls)
        write_json(store.directory / "draft_trace.json", trace)
