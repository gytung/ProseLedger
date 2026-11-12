"""Read a completed, exported run for review without importing executable files."""
import hashlib
import io
import json
import re
import stat
import zipfile
from pathlib import PurePosixPath
from core import HEADINGS, check_audit, digest, split_sections, validate_sources, words

MAX_ARCHIVE = 5_000_000
MAX_EXPANDED = 10_000_000
MAX_FILE = 1_000_000
REQUIRED = {'run.json', 'input.json', 'sources.json', 'initial.md', 'candidate.md',
            'proposal.md', 'checks.json', 'revision_ledger.json'}
OPTIONAL = {'gptzero.json', 'section_candidates.json'}
SECRET_FIELDS = {'apikey', 'authorization', 'accesstoken', 'refreshtoken',
                 'clientsecret', 'password', 'sessiontoken', 'secretkey', 'key'}


def reject_credentials(value):
    if isinstance(value, dict):
        for key, item in value.items():
            normal = re.sub(r'[^a-z]', '', str(key).lower())
            if (normal in SECRET_FIELDS or normal.endswith('apikey')) and isinstance(item, str) and item.strip():
                raise ValueError('The archive contains credential fields. Export a credential-free run.')
            reject_credentials(item)
    elif isinstance(value, list):
        for item in value:
            reject_credentials(item)
    elif isinstance(value, str) and re.search(r'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}', value):
        raise ValueError('The archive contains possible credential material. Import was refused.')


def read_completed_archive(payload):
    if not payload or len(payload) > MAX_ARCHIVE:
        raise ValueError('Choose a completed-run ZIP no larger than 5 MB.')
    result, parsed, prefixes, expanded, seen = {}, {}, set(), 0, set()
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            entries = archive.infolist()
            if not 1 <= len(entries) <= 80:
                raise ValueError('The archive has too many entries.')
            for entry in entries:
                name = entry.filename
                parts = PurePosixPath(name).parts
                if ('\\' in name or '\x00' in name or name.startswith('/')
                        or len(parts) not in (1, 2) or any(p in ('..', '.', '') for p in parts)
                        or ':' in name):
                    raise ValueError('The archive contains an unsafe path.')
                mode = entry.external_attr >> 16
                if stat.S_ISLNK(mode):
                    raise ValueError('Symbolic links are not accepted in run archives.')
                if entry.is_dir():
                    continue
                if entry.flag_bits & 1 or entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                    raise ValueError('Use an unencrypted standard ZIP export.')
                basename = parts[-1]
                if not re.fullmatch(r'[A-Za-z0-9_.-]+\.(?:json|md)', basename):
                    raise ValueError('The archive contains unsupported files.')
                if basename in seen:
                    raise ValueError('The archive contains duplicate record names.')
                seen.add(basename)
                prefixes.add(parts[0] if len(parts) == 2 else '')
                if len(prefixes) > 1:
                    raise ValueError('Import one completed run at a time.')
                expanded += entry.file_size
                if entry.file_size > MAX_FILE or expanded > MAX_EXPANDED:
                    raise ValueError('The expanded archive exceeds the supported size.')
                if entry.file_size > 100_000 and entry.file_size / max(1, entry.compress_size) > 200:
                    raise ValueError('The archive compression ratio is unsupported.')
                raw = archive.read(entry)
                text = raw.decode('utf-8')
                if basename.endswith('.json'):
                    def invalid_constant(value):
                        raise ValueError('The archive contains non-finite numeric values.')
                    data = json.loads(text, parse_constant=invalid_constant)
                    reject_credentials(data)
                    parsed[basename] = data
                else:
                    reject_credentials(text)
                if basename in REQUIRED | OPTIONAL:
                    result[basename] = raw
    except (zipfile.BadZipFile, UnicodeError, json.JSONDecodeError, RuntimeError) as exc:
        raise ValueError('The ZIP export is damaged or contains invalid text records.') from None
    if not REQUIRED <= result.keys():
        raise ValueError('This is not a complete desktop run export. Use Download all records.')
    run, ledger, checks = parsed['run.json'], parsed['revision_ledger.json'], parsed['checks.json']
    if not isinstance(run, dict) or run.get('status') != 'completed' or 'id' in run:
        raise ValueError('Only completed desktop runs can be imported.')
    if not isinstance(run.get('model'), dict) or not isinstance(run.get('newCandidateAccepted'), bool):
        raise ValueError('The run metadata is incomplete.')
    for key in ('initialWords', 'retainedWords', 'changedSections', 'elapsedSeconds'):
        if type(run.get(key)) not in (int, float) or run[key] < 0:
            raise ValueError('The run metrics are invalid.')
    if not isinstance(parsed['input.json'], dict):
        raise ValueError('The original input record is invalid.')
    validate_sources(parsed['sources.json'])
    for name in ('initial.md', 'proposal.md', 'candidate.md'):
        split_sections(result[name].decode('utf-8'))
    original, retained = [result[name].decode('utf-8') for name in ('initial.md', 'proposal.md')]
    if run['initialWords'] != words(original) or run['retainedWords'] != words(retained):
        raise ValueError('The recorded word counts do not match the manuscripts.')
    if (not isinstance(ledger, dict) or ledger.get('originalSHA256') != digest(original)
            or ledger.get('retainedSHA256') != digest(retained)
            or run.get('textSHA256') != digest(retained)):
        raise ValueError('The manuscript hashes do not match the saved run records.')
    edits = ledger.get('edits')
    if not isinstance(edits, list) or len(edits) != 6:
        raise ValueError('The edit ledger is incomplete.')
    originals = split_sections(original)[1]
    retained_sections = split_sections(retained)[1]
    for i, edit in enumerate(edits):
        if not isinstance(edit, dict) or not all(isinstance(edit.get(k), str) for k in ('heading', 'original', 'candidate', 'retained', 'status')):
            raise ValueError('An edit record is malformed.')
        if (edit['heading'] != HEADINGS[i] or edit['original'] != originals[i]['original']
                or edit['retained'] != retained_sections[i]['original']):
            raise ValueError('An edit record does not match its manuscript section.')
        review = edit.get('review')
        if not isinstance(review, dict):
            raise ValueError('A section review is missing.')
        check_audit(review, True)
    if (not isinstance(checks, dict) or not isinstance(checks.get('audit'), dict)
            or not isinstance(checks.get('guard'), dict)
            or type(checks.get('wordRatio')) not in (int, float)
            or not isinstance(checks['guard'].get('findings'), list)
            or not all(isinstance(x, str) for x in checks['guard']['findings'])):
        raise ValueError('The final content-check record is malformed.')
    check_audit(checks['audit'])
    if 'gptzero.json' in parsed:
        data = parsed['gptzero.json']
        if not isinstance(data, dict) or not isinstance(data.get('scans'), dict):
            raise ValueError('The detector record is malformed.')
        for name, scan in data['scans'].items():
            if name not in ('initial', 'proposal') or not isinstance(scan, dict) or not isinstance(scan.get('raw'), dict):
                raise ValueError('The detector record contains unsupported scan entries.')
            if scan.get('textSHA256') != hashlib.sha256(result[name + '.md']).hexdigest():
                raise ValueError('A detector scan does not match the imported manuscript.')
            if 'text' in scan and scan['text'] != result[name + '.md'].decode('utf-8'):
                raise ValueError('A detector scan contains different manuscript text.')
    source_id = next(iter(prefixes)) or 'unprefixed-export'
    lineage, original_source_id = [], source_id
    previous_import = parsed.get('import.json')
    if previous_import is not None:
        if (not isinstance(previous_import, dict)
                or previous_import.get('originalSHA256') != digest(original)
                or previous_import.get('retainedSHA256') != digest(retained)):
            raise ValueError('The previous import provenance does not match the manuscripts.')
        lineage = previous_import.get('importLineage', [])
        if not isinstance(lineage, list) or len(lineage) >= 8:
            raise ValueError('The import provenance chain is invalid or too long.')
        lineage = list(lineage) + [{k: previous_import.get(k) for k in
                                  ('sourceRunId', 'sourceArchiveSHA256', 'importedAtUTC')}]
        for item in lineage:
            if (not isinstance(item, dict) or not isinstance(item.get('sourceRunId'), str)
                    or not 1 <= len(item['sourceRunId']) <= 100
                    or not isinstance(item.get('sourceArchiveSHA256'), str)
                    or not re.fullmatch(r'[a-f0-9]{64}', item['sourceArchiveSHA256'])):
                raise ValueError('The previous import provenance is malformed.')
        original_source_id = previous_import.get('originalSourceRunId', previous_import['sourceRunId'])
        if not isinstance(original_source_id, str) or not 1 <= len(original_source_id) <= 100:
            raise ValueError('The original source identifier is invalid.')
    return result, {'sourceRunId': source_id, 'originalSourceRunId': original_source_id,
                    'importLineage': lineage,
                    'sourceArchiveSHA256': hashlib.sha256(payload).hexdigest(),
                    'originalSHA256': digest(original), 'retainedSHA256': digest(retained),
                    'sourceModel': run['model'], 'importedFiles': sorted(result),
                    'scope': 'Imported completed record for review and optional external validation; no fresh generation or model-response replay.'}
