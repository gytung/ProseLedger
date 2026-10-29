from copy import deepcopy
import json
from pathlib import Path
from proseledger import (
    pipeline,
    memory_planning as sm,
    preservation as revision_verifier,
    revision_controller as runtime,
)
from test_local_executor import TEXT, action, q

SOURCES = [
    {
        "id": "fixture",
        "citation_key": "S1",
        "title": "Invented offline test evidence",
        "content": "Fixture data only. Records may lose a required qualifier.",
    }
]
EMPTY_CATALOG = {
    "schema_version": "v10-semantic-history-binding-2",
    "bank_id": None,
    "bank_sha256": None,
    "cards": [],
    "skipped": [],
    "budget": {"max_chars": 20000, "max_example_chars": 3200, "used_chars": 2},
}


def memory_catalog():
    return {
        **deepcopy(EMPTY_CATALOG),
        "bank_id": "SYNTHETIC_OFFLINE_FIXTURE",
        "cards": [
            {
                "id": "fixture_concrete",
                "dimensions": ["empty_framing"],
                "operation": "Rephrase existing content.",
                "steps": ["A concrete statement already exists."],
                "preserve": ["Existing meaning"],
                "conditions": [
                    {"id": "R1", "kind": "required", "text": "An existing concrete statement."}
                ],
                "counterexamples": [],
                "examples": [
                    {
                        "episode_id": "synthetic-example",
                        "payload": {
                            "before": "SYNTHETIC before [S1]",
                            "after": "SYNTHETIC after [S1]",
                            "label": "unit-test fixture, not actual research evidence",
                        },
                    }
                ],
            }
        ],
    }


class FakeStore:
    """No client, keys or network. Cache file layout matches original CallStore."""

    is_test_fixture = True
    model = "offline-runtime-fixture"

    def __init__(
        self,
        directory,
        *,
        plan_mode="valid",
        patch_mode="valid",
        fail_once=None,
        fail_after_cache=None
    ):
        self.directory = Path(directory)
        self.cache = self.directory / "call_cache"
        self.cache.mkdir(parents=True)
        self.calls, self.events, self.requests, self.fresh_generations = [], [], [], []
        self.plan_mode, self.patch_mode = plan_mode, patch_mode
        self.fail_once, self.fail_after_cache = fail_once, fail_after_cache

    def status(self, *args, **kwargs):
        pass

    def event(self, kind, **kwargs):
        self.events.append({"event": kind, **kwargs})

    def ask(self, name, prompt):
        request = {
            "version": pipeline.VERSION,
            "agent": name,
            "model": self.model,
            "messages": [{"role": "human", "content": prompt}],
        }
        digest = pipeline.input_hash(request)
        path = self.cache / (digest + ".json")
        self.requests.append((name, prompt))
        if path.exists():
            saved = json.loads(path.read_bytes())
            assert saved["request"] == request
            raw, cached = saved["response"]["content"], True
        else:
            if name == self.fail_once:
                self.fail_once = None
                self.event("fake_transport_failure", agent=name)
                raise RuntimeError("Simulated failure before a response exists")
            self.fresh_generations.append((name, digest))
            raw, cached = self._response(name, prompt), False
            path.write_text(
                json.dumps(
                    {"request": request, "input_hash": digest, "response": {"content": raw}}
                ),
                encoding="utf-8",
            )
        self.calls.append(
            {
                "agent": name,
                "input_hash": digest,
                "cached": cached,
                "cache_file": str(path),
                "usage": {"total_tokens": 17},
                "is_test_fixture": True,
            }
        )
        if name == self.fail_after_cache:
            self.fail_after_cache = None
            raise RuntimeError(
                "Simulated interruption after cache commit, before returning response"
            )
        return raw

    def ask_json(self, name, prompt, validator):
        return validator(pipeline.parse_json_response(self.ask(name, prompt)))

    def _response(self, name, prompt):
        if name == "style_judge":
            return json.dumps(
                {
                    "dimensions": {
                        dimension: {
                            "score": 2,
                            "evidence": [],
                            "suggestion": "Synthetic offline fixed score, not an actual assessment.",
                        }
                        for dimension in pipeline.JUDGE_DIMENSIONS
                    }
                }
            )
        if name == "anonymous_revision_fidelity_v6":
            return json.dumps(
                {
                    "verdict": "preserved",
                    "issues": [],
                    "explanation": "Synthetic fixture verdict for testing common-function wiring.",
                }
            )
        if name.startswith("semantic_planner_round_"):
            data = json.loads(
                prompt.split("The following JSON is task data, not instructions:\n")[1]
            )
            if self.plan_mode == "invalid":
                return "not JSON, raw failure retained"
            if self.plan_mode == "empty":
                return json.dumps(
                    {"actions": [], "card_reviews": [], "abstention_reason": "No safe edit."}
                )
            paragraph = next(
                p
                for p in sm.provenance._paragraphs(data["current_manuscript"])
                if p["section"] == "Introduction"
            )
            target = q("Introduction", paragraph["quote"])
            a = action([target])
            reviews = []
            if data["historical_catalog"]:
                card = data["historical_catalog"][0]
                a["memory_card_ids"] = [card["id"]]
                a["correspondence"]["historical_pattern"] = "Fixture historical pattern."
                a["condition_checks"] = [
                    {
                        "condition_id": "R1",
                        "status": "supported",
                        "evidence": [target],
                        "reason": "Fixture applicability only.",
                    }
                ]
                reviews = [
                    {
                        "card_id": card["id"],
                        "applicability": "applicable",
                        "current_quotes": [target],
                        "reason": "Synthetic current correspondence.",
                    }
                ]
            actions = [a]
            if self.plan_mode == "overlap":
                first = q("Introduction", paragraph["quote"].split(". ")[0] + ".")
                second = q("Introduction", "We will examine two formats [S1].")
                first_action = deepcopy(a)
                first_action["targets"] = [first]
                actions = [first_action, action([second])]
            if self.plan_mode == "partial_invalid":
                actions.append(action([q("Introduction", "This quote does not exist.")]))
            return json.dumps(
                {"actions": actions, "card_reviews": reviews, "abstention_reason": ""}
            )
        if name.startswith("semantic_patch_writer_round_"):
            data = json.loads(
                prompt.split("The following JSON is task data, not instructions:\n")[1]
            )
            if self.patch_mode == "invalid":
                return "A full draft is not a patch.\n"
            edits = []
            for w in data["authorized_paragraphs"]:
                replacement = w["before"]
                if self.patch_mode != "identity":
                    if "Records can lose a required qualifier." in replacement:
                        replacement = replacement.replace(
                            "Records can lose a required qualifier.",
                            "A required qualifier can be lost from a record.",
                        )
                    else:
                        replacement = replacement.replace(
                            "A required qualifier can be lost from a record.",
                            "A record may lose a required qualifier.",
                        )
                edits.append(
                    {"target_id": w["target_id"], "before": w["before"], "replacement": replacement}
                )
            return json.dumps(
                {
                    "schema_version": data["schema_version"],
                    "base_sha256": data["base_sha256"],
                    "contract_sha256": data["contract_sha256"],
                    "edits": edits,
                }
            )
        raise AssertionError("Unexpected attempted model role: " + name)


def warmup_records(store, *, rejected=False):
    initial = pipeline.evaluate_version(store, TEXT, 0, SOURCES)
    warm_text = TEXT.replace(
        "This proposal compares two record formats.", "Two record formats will be compared."
    )
    candidate = pipeline.evaluate_version(store, warm_text, 1, SOURCES)
    guard = revision_verifier.check_content_preservation(store, TEXT, warm_text, SOURCES)
    if rejected:
        guard = {**guard, "passed": False, "issues": ["Synthetic preexisting warm-up rejection."]}
    accepted, selected = pipeline.select_candidate(initial, candidate, guard)
    candidate.update(
        guard=guard,
        accepted=accepted,
        branch="targeted",
        effective_generator_agent="targeted_rewriter_round_1",
        previous_text_hash=initial["text_hash"],
        original_text=initial["text"],
        selected_text_hash=selected["text_hash"],
        selected_score=deepcopy(selected["score"]),
    )
    return initial, candidate
