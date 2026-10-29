"""Isolated local jobs, explicit source preparation, and resumable run state."""

from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(os.environ.get("PROSELEDGER_DATA_DIR", str(ROOT))).expanduser().resolve()
RUNS = WORK / "runs"


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def prepare_sources(output: Path, sources: list) -> Path:
    """Persist uploaded evidence bytes before the backend validates provenance."""
    clean = []
    for item in sources:
        source = {key: value for key, value in item.items() if key != "_pdf_bytes"}
        if "_pdf_bytes" in item:
            original = item["_pdf_bytes"]
            digest = hashlib.sha256(original).hexdigest()
            if digest != source.get("pdf_sha256"):
                raise ValueError(
                    "The uploaded PDF changed during preparation. Please upload it again."
                )
            relative = f"sources/{digest}.pdf"
            destination = output / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(original)
            source["pdf_file"] = relative
            source["url"] = f"local-pdf://sha256/{digest}"
        clean.append(source)
    source_path = output / "supplied_sources.json"
    source_path.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
    from proseledger.pipeline import load_sources

    load_sources(source_path)
    return source_path


def launch_worker(output: Path):
    config = output / "job_config.json"
    flags = (
        (subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP)
        if os.name == "nt"
        else 0
    )
    with (output / "console.log").open("ab") as log:
        process = subprocess.Popen(
            [sys.executable, str(ROOT / "ui" / "job_worker.py"), str(config)],
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=flags,
            start_new_session=(os.name != "nt"),
        )
    (output / "pid.txt").write_text(str(process.pid), encoding="ascii")


def attempt_number(output: Path, job: dict) -> int:
    """Older job records have no attempt field; count their preserved archives."""
    archived = []
    for path in output.glob("attempt_*.json"):
        match = re.fullmatch(r"attempt_(\d+)\.json", path.name)
        if match:
            archived.append(int(match.group(1)))
    inferred = max(archived, default=0) + 1
    return max(int(job.get("attempt", inferred)), inferred)


def resume_job(output: Path):
    """Resume the same immutable inputs and engine directory; never erase its cache."""
    previous = read_json(output / "job.json", {})
    if previous.get("status") in ("starting", "running", "completed"):
        raise ValueError("Only a stopped, incomplete run can be resumed.")
    config_path = output / "job_config.json"
    config = read_json(config_path, {})
    command = config.get("command", [])
    if not isinstance(command, list) or "--output" not in command:
        raise ValueError(
            "The original run configuration is missing. Keep this folder for diagnosis."
        )
    attempt = attempt_number(output, previous)
    archive = output / f"attempt_{attempt:03d}.json"
    if archive.exists():
        if read_json(archive) != previous:
            raise ValueError(
                "A previous attempt record already exists with different contents. No files were overwritten."
            )
    else:
        archive.write_text(json.dumps(previous, indent=2), encoding="utf-8")
    if "--resume" not in command:
        command.append("--resume")
    config["command"] = command
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    now = datetime.now(timezone.utc).isoformat()
    state = {
        "status": "starting",
        "mode": previous.get("mode", "live"),
        "attempt": attempt + 1,
        "started_at": now,
        "first_started_at": previous.get("first_started_at", previous.get("started_at", now)),
    }
    (output / "job.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    try:
        launch_worker(output)
    except Exception as exc:
        state.update(
            status="failed",
            error_type=type(exc).__name__,
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        (output / "job.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
        raise


def latest_job(mode: str) -> Path | None:
    entry = read_json(RUNS / f"latest_{mode}.json", {})
    name = entry.get("path")
    if not isinstance(name, str) or Path(name).name != name:
        return None
    output = RUNS / name
    return output if output.is_dir() else None


def is_running(mode: str) -> bool:
    current = latest_job(mode)
    return bool(
        current and read_json(current / "job.json", {}).get("status") in ("running", "starting")
    )


def run_progress(output: Path, job: dict) -> dict:
    """Count physical completed calls across attempts; cache hits are not new calls."""
    events_path = output / "output" / "events.jsonl"
    completed = set()
    failed = 0
    latest_agent = ""
    first_event = None
    try:
        for index, line in enumerate(events_path.read_text(encoding="utf-8").splitlines()):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue  # A writer may still be appending the last line.
            if first_event is None:
                first_event = event.get("time")
            if event.get("event") == "model_call_completed":
                completed.add(event.get("input_hash") or f"record-{index}")
            elif event.get("event") == "model_call_failed":
                failed += 1
            if event.get("event") == "model_call_started":
                latest_agent = str(event.get("agent", ""))
    except OSError:
        pass
    timestamps = [job.get("first_started_at"), job.get("started_at"), first_event]
    for archive in output.glob("attempt_*.json"):
        old = read_json(archive, {})
        timestamps.extend([old.get("first_started_at"), old.get("started_at")])
    parsed = []
    for timestamp in timestamps:
        if not timestamp:
            continue
        try:
            value = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
            parsed.append(value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value)
        except ValueError:
            continue
    end = datetime.now(timezone.utc)
    if job.get("status") in ("completed", "failed") and job.get("finished_at"):
        try:
            end = datetime.fromisoformat(job["finished_at"].replace("Z", "+00:00"))
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    seconds = max(0, int((end - min(parsed)).total_seconds())) if parsed else 0
    return {
        "completed_calls": len(completed),
        "failed_calls": failed,
        "elapsed_seconds": seconds,
        "elapsed_label": f"{seconds // 3600:d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}",
        "latest_agent": latest_agent,
        "attempt": attempt_number(output, job),
    }


def pdf_sources(files) -> list:
    from pypdf import PdfReader

    sources = []
    seen_digests = set()
    seen_titles = set()
    for index, upload in enumerate(files, 1):
        original = upload.getvalue()
        digest = hashlib.sha256(original).hexdigest()
        if digest in seen_digests:
            raise ValueError(
                f"{upload.name}: the same PDF was supplied twice. Please choose different papers."
            )
        seen_digests.add(digest)
        reader = PdfReader(io.BytesIO(original))
        if reader.is_encrypted:
            raise ValueError(
                f"{upload.name}: encrypted PDFs are not supported. Supply an unlocked file."
            )
        parts = []
        size = 0
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                parts.append(text)
                size += len(text)
            if size >= 20000:
                break
        content = "\n\n".join(parts)[:20000].strip()
        if len(content) < 200:
            raise ValueError(
                f"{upload.name}: not enough readable text. Scanned PDFs need OCR before upload."
            )
        metadata = reader.metadata or {}
        raw_title = str(metadata.get("/Title") or Path(upload.name).stem)
        title = raw_title if raw_title.strip() and len(raw_title) < 400 else Path(upload.name).stem
        if title in seen_titles:
            title = f"{title} [{Path(upload.name).stem} · Source {index}]"
        seen_titles.add(title)
        sources.append(
            {
                "id": f"S{index}",
                "citation_key": f"S{index}",
                "num": index,
                "title": title,
                "content": content,
                "content_kind": "user_supplied_pdf_excerpt",
                "evidence_scope": "First 20,000 extracted characters at most; supplied evidence, not independently verified.",
                "original_filename": Path(upload.name).name,
                "url": f"local-pdf://sha256/{digest}",
                "pdf_sha256": digest,
                "pdf_file": f"sources/{digest}.pdf",
                "_pdf_bytes": original,
            }
        )
    return sources


def new_job(topic: str, sources: list) -> Path:
    """Start one fresh run without replacing any earlier result."""
    run_id = f"live_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    output = RUNS / run_id
    output.mkdir(parents=True, exist_ok=False)
    source_path = prepare_sources(output, sources)
    command = [
        sys.executable,
        "-m",
        "proseledger",
        "run",
        "--output",
        str(output / "output"),
        "--sources",
        str(source_path),
        "--topic",
        topic,
    ]
    config = {"command": command, "cwd": str(ROOT), "output": str(output)}
    (output / "job_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    now = datetime.now(timezone.utc).isoformat()
    state = {
        "status": "starting",
        "mode": "live",
        "attempt": 1,
        "started_at": now,
        "first_started_at": now,
    }
    (output / "job.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    try:
        launch_worker(output)
    except Exception:
        state["status"] = "failed"
        (output / "job.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
        raise
    (RUNS / "latest_live.json").write_text(json.dumps({"path": output.name}), encoding="utf-8")
    return output
