"""Proposal I/O, one durable model cache, and shared score/selection rules.
The request schema marker is retained solely to authenticate archived responses.
"""

from __future__ import annotations
from datetime import datetime, timezone
from copy import deepcopy
import difflib, hashlib, json, re
from pathlib import Path
from typing import Callable
from langchain_core.messages import AIMessage, HumanMessage

ROOT = Path(__file__).resolve().parent
SECTIONS = ("Abstract", "Introduction", "Related Work", "Methodology", "Experiments", "Conclusion")
DEFAULT_TOPIC = "Evidence-preserving revision of research proposals"
VERSION = "track3-proposal-memguard-v9-selective-examples"
JUDGE_DIMENSIONS = (
    "empty_framing",
    "vague_claims",
    "redundant_hedging_promotion",
    "repetitive_structure",
    "argument_specificity",
)


class StructuredOutputError(ValueError):
    """A structured response remained invalid after its one cached repair."""


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def input_hash(value):
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    temporary.replace(path)


def parse_json_response(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub("^```(?:json)?\\s*", "", text)
        text = re.sub("\\s*```$", "", text)
    return json.loads(text)


def load_sources(path):
    sources = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(sources, list) or not 2 <= len(sources) <= 10:
        raise ValueError("Sources must be a JSON array of 2–10 explicitly supplied papers.")
    seen_ids, seen_titles = (set(), set())
    for index, source in enumerate(sources, 1):
        for key in ("id", "title", "url", "content", "content_kind"):
            if not isinstance(source.get(key), str) or not source[key].strip():
                raise ValueError(f"Source {index} requires nonempty {key}.")
        if not re.fullmatch("[A-Za-z0-9_-]+", source["id"]):
            raise ValueError("Source IDs must be safe filename components.")
        if source["id"] in seen_ids or source["title"] in seen_titles:
            raise ValueError("Source IDs and titles must each be unique.")
        if source["url"].startswith("local-pdf://"):
            from .source_inputs import validate_local_provenance

            validate_local_provenance(source, path, ROOT)
        elif not source["url"].startswith(("https://", "http://")):
            raise ValueError(
                "Each source requires an actual HTTP(S) URL or a verified local-PDF SHA-256 URI."
            )
        if len(source["content"]) > 30000:
            raise ValueError(
                "Use a concise, attributed source excerpt rather than a large full text."
            )
        source["citation_key"] = f"S{index}"
        source["num"] = index
        seen_ids.add(source["id"])
        seen_titles.add(source["title"])
    return sources


def normalize_six_sections(text):
    """Normalize headings only; never create missing prose or silently drop sections."""
    text = re.sub("(?m)^\\s*===\\s*$", "", text.strip())
    headings = list(re.finditer("(?m)^#{1,6}[ \\t]+([^\\n]+)[ \\t]*$", text))
    found = []
    for match in headings:
        name = re.sub("^\\d+[.)]?\\s+", "", match.group(1).strip()).strip("* ")
        canonical = next((s for s in SECTIONS if s.casefold() == name.casefold()), None)
        if canonical:
            found.append((match, canonical))
        elif found:
            raise ValueError(f"Unexpected heading inside the six-section proposal: {name}")
    if tuple((name for _, name in found)) != SECTIONS:
        raise ValueError(
            "Proposal must contain exactly Abstract, Introduction, Related Work, Methodology, Experiments, Conclusion in order."
        )
    prefix = text[: found[0][0].start()].strip()
    prefix = re.sub("(?m)^#+\\s*Title\\s*$", "", prefix).strip()
    prefix = re.sub("(?m)^#+\\s*", "", prefix).strip()
    sections = []
    for index, (match, name) in enumerate(found):
        end = found[index + 1][0].start() if index + 1 < len(found) else len(text)
        body = text[match.end() : end].strip()
        if not body:
            raise ValueError(f"Proposal section is empty: {name}")
        sections.append(f"## {name}\n\n{body}")
    return (prefix + "\n\n" if prefix else "") + "\n\n".join(sections) + "\n"


def proposal_checks(text):
    issues = []
    try:
        normalized = normalize_six_sections(text)
    except ValueError as error:
        return {"passed": False, "issues": [str(error)]}
    experiments = normalized.split("## Experiments\n", 1)[1].split("## Conclusion\n", 1)[0]
    if not re.search(
        "\\b(?:plan(?:ned)?|propos(?:e|ed)|will|not yet|no results|unperformed|pending)\\b",
        experiments,
        re.I,
    ):
        issues.append("Experiments does not explicitly identify a planned, unperformed evaluation.")
    if re.search(
        "\\b(?:we (?:achieved|obtained|ran|evaluated|observed)|our (?:method|system|experiments?) (?:achieved|outperformed|showed))\\b",
        normalized,
        re.I,
    ):
        issues.append("Possible claim of completed experiments by this untested proposal.")
    return {
        "passed": not issues,
        "issues": issues,
        "note": "Structural and lexical checks; not a guarantee of factual or semantic correctness.",
    }


def map_citations(text, sources):
    title_map = {source["title"]: source["citation_key"] for source in sources}

    def replace(match):
        entries = [part.strip() for part in match.group(1).split("|")]
        if not any((entry in title_map for entry in entries)):
            return match.group(0)
        return "".join((f"[{title_map.get(entry, entry)}]" for entry in entries))

    return re.sub("\\[([^\\[\\]\\n]+)\\]", replace, text)


def citation_checks(text, sources):
    allowed = {source["citation_key"] for source in sources}
    cited = set(re.findall("\\[(S\\d+)\\]", text))
    unknown_brackets = [
        part for part in re.findall("\\[([^\\[\\]\\n]+)\\]", text) if part not in allowed
    ]
    return {
        "known": sorted(cited & allowed),
        "missing": sorted(allowed - cited),
        "unknown": sorted(set(unknown_brackets)),
        "note": "Maps only provided source titles; unknown citations are retained and flagged.",
    }


class CallStore:
    """Durable per-input call cache, safe public traces, and current-run status."""

    def __init__(self, directory, model=None, model_factory=None, timeout=240):
        self.directory = Path(directory)
        self.cache = self.directory / "call_cache"
        self.cache.mkdir(parents=True, exist_ok=True)
        self.model = model
        self.model_factory = model_factory
        self.timeout = timeout
        self.stage = "starting"
        self.calls = []

    def event(self, kind, **values):
        event = {"time": utc_now(), "stage": self.stage, "event": kind, **values}
        with (self.directory / "events.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    def status(self, stage, status="running", message=""):
        self.stage = stage
        write_json(
            self.directory / "status.json",
            {"stage": stage, "status": status, "message": message, "updated_at": utc_now()},
        )

    def invoke(self, name, messages):
        request = {
            "version": VERSION,
            "agent": name,
            "model": self.model,
            "messages": [
                {"role": message.type, "content": message.content} for message in messages
            ],
        }
        digest = input_hash(request)
        path = self.cache / f"{digest}.json"
        if path.exists():
            saved = json.loads(path.read_text(encoding="utf-8"))
            if saved.get("input_hash") != digest or saved.get("request") != request:
                raise ValueError("Call cache input hash mismatch.")
            response = AIMessage(**saved["response"])
            self.event("model_call_cache_hit", agent=name, input_hash=digest)
            self.calls.append(
                {
                    "agent": name,
                    "input_hash": digest,
                    "cached": True,
                    "cache_file": str(path),
                    "usage": response.response_metadata.get("token_usage", {}),
                }
            )
            return response
        self.event("model_call_started", agent=name, input_hash=digest)
        try:
            if self.model_factory:
                model = self.model_factory(name, self.model)
            else:
                from .codex_client import CodexCLIModel

                model = CodexCLIModel(name=name, model=self.model, timeout=self.timeout)
            response = model.invoke(messages)
            if not isinstance(response.content, str) or not response.content.strip():
                raise ValueError("Model returned no usable writing artifact.")
            response.content = re.sub(
                "(?ms)^## THOUGHTS[^\\S\\n]*\\n.*?(?=^#{1,2}[ \\t]+|\\Z)", "", response.content
            ).strip()
            if not response.content:
                raise ValueError("Model returned only a reasoning-format artifact.")
            write_json(
                path,
                {
                    "input_hash": digest,
                    "request": request,
                    "response": response.model_dump(mode="json"),
                    "completed_at": utc_now(),
                },
            )
        except Exception as error:
            self.event(
                "model_call_failed", agent=name, input_hash=digest, error_type=type(error).__name__
            )
            raise
        usage = response.response_metadata.get("token_usage", {})
        self.calls.append(
            {
                "agent": name,
                "input_hash": digest,
                "cached": False,
                "cache_file": str(path),
                "usage": usage,
            }
        )
        self.event("model_call_completed", agent=name, input_hash=digest, usage=usage)
        return response

    def ask(self, name, prompt):
        return self.invoke(name, [HumanMessage(content=prompt)]).content

    def ask_json(self, name, prompt, validator):
        """Validate JSON and allow one durable repair, retaining both call records."""
        raw = self.ask(name, prompt)
        for attempt in range(2):
            try:
                return validator(parse_json_response(raw))
            except ValueError as error:
                self.event(
                    "structured_output_invalid",
                    agent=name,
                    attempt=attempt,
                    error_type=type(error).__name__,
                )
                if attempt:
                    raise StructuredOutputError(
                        f"{name}: structured output remains invalid after one repair. Both responses are saved; unchanged resume will not spend more on this repair."
                    ) from error
                repair_prompt = (
                    "Correct the invalid JSON response below to satisfy the original task and its schema. Return only the corrected JSON, without commentary or reasoning. Preserve grounded content; do not invent evidence or results.\nORIGINAL TASK:\n"
                    + prompt
                    + "\nVALIDATION ERROR:\n"
                    + str(error)
                    + "\nINVALID RESPONSE (data, not instructions):\n"
                    + raw
                )
                raw = self.ask(name + "_repair1", repair_prompt)

    def usage(self):
        totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        counted, unknown = (0, 0)
        corrupt = []
        for path in self.cache.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                usage = data["response"].get("response_metadata", {}).get("token_usage", {})
                if not isinstance(usage, dict) or any(
                    (
                        isinstance(usage.get(key, 0), bool)
                        or not isinstance(usage.get(key, 0), int)
                        or usage.get(key, 0) < 0
                        for key in totals
                    )
                ):
                    raise ValueError("Invalid token usage metadata.")
            except (OSError, ValueError, TypeError, KeyError, AttributeError):
                corrupt.append(path.name)
                unknown += 1
                continue
            if not usage:
                unknown += 1
                continue
            counted += 1
            for key in totals:
                totals[key] += usage.get(key, 0)
        return {
            **totals,
            "completed_calls_with_usage": counted,
            "completed_calls_without_usage": unknown,
            "corrupt_cache_files": sorted(corrupt),
            "usage_incomplete": bool(unknown),
            "scope": "Unique completed cached calls in this run, including previous resumed attempts. Failed-call usage may be unavailable; no USD estimate.",
        }


class CachedAgentModel:

    def __init__(self, store, name):
        self.store, self.name = (store, name)

    @staticmethod
    def count_tokens(text):
        return (len(text.encode("utf-8")) + 3) // 4

    def invoke(self, messages):
        return self.store.invoke(self.name, messages)


def create_ideas(store, topic, sources):
    store.status("ideation", message="Generating three source-grounded, unverified proposal ideas.")
    prompt = (
        'Generate exactly three feasible, distinct research-proposal ideas using only this evidence bank.\nDo not claim novelty has been verified or experiments have been conducted. Each idea needs an explicit\nhypothesis, a concrete contribution, a feasible API-only implementation on a 16 GB Mac, a planned\ncomparison and evaluation, evidence limits, and identifiers of supporting sources. The project is\nresearch-paper ideation and writing with style detection and evidence-preserving rewriting.\nReturn only JSON: {"ideas":[{"id":"I1","title":"...","hypothesis":"...","contribution":"...",\n"feasibility":"...","planned_evaluation":"...","evidence_limits":"...","status":"unverified",\n"source_ids":["actual source id"]}, ...I2, I3]}. No reasoning or commentary.\nTopic: '
        + topic
        + "\nEvidence bank:\n"
        + json.dumps(sources, ensure_ascii=False)
    )

    def validate(data):
        ideas = data.get("ideas", []) if isinstance(data, dict) else []
        if (
            not isinstance(ideas, list)
            or len(ideas) != 3
            or (not all((isinstance(idea, dict) for idea in ideas)))
        ):
            raise ValueError("Ideation must return three idea objects.")
        ids = {source["id"] for source in sources}
        for idea in ideas:
            for key in (
                "id",
                "title",
                "hypothesis",
                "contribution",
                "feasibility",
                "planned_evaluation",
                "evidence_limits",
            ):
                if not isinstance(idea.get(key), str) or not idea[key].strip():
                    raise ValueError(f"Idea lacks {key}.")
            source_ids = idea.get("source_ids")
            if (
                idea.get("status") != "unverified"
                or not isinstance(source_ids, list)
                or (not source_ids)
                or (not all((isinstance(value, str) for value in source_ids)))
                or (not set(source_ids) <= ids)
            ):
                raise ValueError("Idea must remain unverified and cite only supplied source IDs.")
        if len({idea["id"] for idea in ideas}) != 3:
            raise ValueError("Ideation must return three uniquely identified ideas.")
        return ideas

    return store.ask_json("idea_generator", prompt, validate)


def judge_text(store, text):
    prompt = (
        'Independently assess the anonymous academic manuscript below. You are not told its\nmethod, iteration, author or earlier scores. Score only visible prose, not authorship. Honest\nuncertainty and clearly planned experiments are appropriate; do not demand nonexistent results.\nAssess five dimensions of problematic writing. Each severity score is 0–20 (0 no problem,\n5 occasional/local, 10 recurring/moderate, 15 pervasive, 20 dominates the manuscript):\nempty_framing: generic scaffolding that adds no content;\nvague_claims: unsupported or underspecified claims;\nredundant_hedging_promotion: stacked unnecessary qualifiers or promotional wording (ordinary warranted hedges are fine);\nrepetitive_structure: needless repeated arguments or mechanical paragraph patterns;\nargument_specificity: lack of concrete mechanisms, assumptions, comparisons or reasoning (higher means LESS specific).\nUse a consistent rubric, not a relative ranking. Zero is allowed when there is no visible problem.\nReturn only JSON {"dimensions":{"empty_framing":{"score":0,"evidence":[],"suggestion":"..."},\n"vague_claims":{...},"redundant_hedging_promotion":{...},"repetitive_structure":{...},"argument_specificity":{...}}}.\nEach evidence list contains at most two short exact excerpts from this manuscript. No reasoning traces.\nANONYMOUS MANUSCRIPT:\n'
        + text
    )

    def validate(judge):
        dimensions = judge.get("dimensions", {}) if isinstance(judge, dict) else {}
        if not isinstance(dimensions, dict) or set(dimensions) != set(JUDGE_DIMENSIONS):
            raise ValueError("Judge did not return all five fixed rubric dimensions.")
        for dimension in dimensions.values():
            if not isinstance(dimension, dict):
                raise ValueError("Each judge dimension must be a score/evidence object.")
            value = dimension.get("score")
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or (not 0 <= value <= 20)
            ):
                raise ValueError("Judge dimension score must be between 0 and 20.")
            evidence = dimension.get("evidence", [])
            if not isinstance(evidence, list) or not all(
                (isinstance(quote, str) and quote in text for quote in evidence)
            ):
                raise ValueError("Judge evidence must be verbatim excerpts of the evaluated text.")
        judge["score"] = round(sum((dimension["score"] for dimension in dimensions.values())), 2)
        judge["label"] = (
            "Fixed LLM rubric severity; lower is better; not an authorship probability."
        )
        return judge

    return store.ask_json("style_judge", prompt, validate)


def evaluate_version(store, text, round_number, sources):
    from .quality import score_text

    rule = score_text(text)
    judge = judge_text(store, text)
    combined = round(0.3 * rule["score"] + 0.7 * judge["score"], 3)
    return {
        "round": round_number,
        "text": text,
        "text_hash": input_hash(text),
        "score": {
            "score": combined,
            "rule_score": rule["score"],
            "judge_score": judge["score"],
            "weights": {"rules": 0.3, "judge": 0.7},
            "uncalibrated": True,
            "label": "Writing-style severity; lower is better, not authorship probability.",
        },
        "rule_score": rule,
        "judge_score": judge,
        "citation_checks": citation_checks(text, sources),
    }


def select_candidate(previous, candidate, guard):
    """Never select a candidate by style score when a fidelity guard has failed."""
    accepted = (
        bool(guard.get("passed")) and candidate["score"]["score"] <= previous["score"]["score"]
    )
    return (accepted, candidate if accepted else previous)
