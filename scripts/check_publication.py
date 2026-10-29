"""Validate public artifacts, provenance and recorded results without model calls."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SKIP = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "runs",
    "uploads",
}
TEXT_TYPES = {".py", ".md", ".json", ".html", ".csv", ".txt", ".toml", ".yml", ".yaml"}


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    issues = []
    checked = 0
    patterns = {
        "personal macOS path": re.compile(r"/Users/[A-Za-z0-9][^/\\\s]+/"),
        "private key material": re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
        ),
        "credential-shaped token": re.compile(
            r"\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{30,}|gh[pousr]_[A-Za-z0-9]{30,})\b"
        ),
        "non-English source literal": re.compile(r"[\u4e00-\u9fff]"),
    }
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if any(part in SKIP for part in relative.parts):
            continue
        if path.is_symlink():
            issues.append(f"{relative}: symbolic link")
            continue
        if not path.is_file():
            continue
        if not relative.as_posix().isascii():
            issues.append(f"{relative}: non-ASCII file name")
        if (
            path.name in {"auth.json", "credentials.json", "secrets.toml"}
            or "call_cache" in relative.parts
        ):
            issues.append(f"{relative}: private runtime artifact")
        if path.suffix not in TEXT_TYPES and path.name not in {
            "LICENSE",
            ".gitignore",
            ".gitattributes",
            ".editorconfig",
        }:
            continue
        text = path.read_text(encoding="utf-8")
        checked += 1
        for label, pattern in patterns.items():
            if pattern.search(text):
                issues.append(f"{relative}: {label}")

    evidence = json.loads((ROOT / "docs/evidence.json").read_text(encoding="utf-8"))
    page = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    embedded = re.search(
        r'<script id="data" type="application/json">(.*?)</script>', page, re.S
    )
    if not embedded or json.loads(embedded.group(1)) != evidence:
        issues.append("docs: viewer data and evidence JSON differ")

    cases = evidence["cases"]
    if len(cases) != 6:
        issues.append("docs: expected the complete six-case batch")
    decisions = 0
    outcomes = {"wins": 0, "ties": 0, "losses": 0}
    for case in cases:
        for name, record in [("initial", case["initial"]), *case["branches"].items()]:
            if digest(record["text"]) != record["text_sha256"]:
                issues.append(f"Case {case['id']}/{name}: text hash differs")
            for decision in record.get("rounds", []):
                decisions += 1
                if (
                    digest(decision["candidate_text"])
                    != decision["candidate_text_sha256"]
                ):
                    issues.append(f"Case {case['id']}/{name}: candidate hash differs")
        delta = (
            case["branches"]["memory"]["score"] - case["branches"]["targeted"]["score"]
        )
        outcomes["wins" if delta < -1e-8 else "losses" if delta > 1e-8 else "ties"] += 1
    for method in ("targeted", "planner", "memory"):
        mean = sum(c["branches"][method]["score"] for c in cases) / len(cases)
        if not math.isclose(mean, evidence["summary"]["means"][method], abs_tol=1e-8):
            issues.append(f"docs: incorrect {method} mean")
    if decisions != 54 or outcomes != {"wins": 0, "ties": 4, "losses": 2}:
        issues.append("docs: decision count or win/tie/loss summary differs")
    notice = (ROOT / "proseledger/drafting/LICENSE").read_text(encoding="utf-8")
    if "Copyright (c) 2025 lira-workflow" not in notice:
        issues.append("drafting: required original copyright notice missing")
    for name in ("README.md", "THIRD_PARTY_NOTICES.md", "docs/PUBLISHING.md"):
        if not (ROOT / name).is_file():
            issues.append(f"{name}: required release document missing")

    print(
        json.dumps(
            {
                "status": "failed" if issues else "passed",
                "text_files_checked": checked,
                "recorded_cases": len(cases),
                "recorded_decisions": decisions,
                "new_model_calls": 0,
                "issues": issues,
            },
            indent=2,
        )
    )
    return int(bool(issues))


if __name__ == "__main__":
    sys.exit(main())
