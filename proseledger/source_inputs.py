"""Read explicit source JSON and verify any supplied local PDF by its digest."""

import hashlib, re
from pathlib import Path


def validate_local_provenance(source, source_json, root):
    match = re.fullmatch(r"local-pdf://sha256/([0-9a-f]{64})", source["url"])
    if not match or source.get("pdf_sha256") != match.group(1):
        raise ValueError("Local PDF source needs its matching SHA-256 URI and pdf_sha256.")
    relative = Path(source.get("pdf_file", ""))
    if relative.is_absolute() or ".." in relative.parts or not str(relative):
        raise ValueError("pdf_file must be relative to the source JSON folder.")
    parent = Path(source_json).resolve().parent
    path = (parent / relative).resolve()
    if not path.is_relative_to(parent) or not path.is_file():
        raise ValueError("Supplied local PDF is missing from the source JSON folder.")
    if hashlib.sha256(path.read_bytes()).hexdigest() != match.group(1):
        raise ValueError("Supplied local PDF SHA-256 mismatch.")
