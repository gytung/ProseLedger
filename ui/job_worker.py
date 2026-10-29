"""Keep an explicit engine run alive after the browser disconnects."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone


def main() -> int:
    config_path = Path(sys.argv[1]).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output = Path(config["output"]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    completion = output / "job.json"
    try:
        previous = json.loads(completion.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        previous = {}
    now = datetime.now(timezone.utc).isoformat()
    report = {
        "started_at": previous.get("started_at", now),
        "first_started_at": previous.get("first_started_at", previous.get("started_at", now)),
        "attempt": int(previous.get("attempt", 1)),
        "mode": previous.get("mode", "live"),
        "status": "running",
    }
    completion.write_text(json.dumps(report, indent=2), encoding="utf-8")
    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(config["command"], cwd=config["cwd"], creationflags=flags)
        report.update(
            status="completed" if result.returncode == 0 else "failed", returncode=result.returncode
        )
    except Exception as exc:
        report.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    tmp = completion.with_suffix(".tmp")
    tmp.write_text(json.dumps(report, indent=2), encoding="utf-8")
    tmp.replace(completion)
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
