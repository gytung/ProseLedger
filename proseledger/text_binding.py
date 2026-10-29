from collections.abc import Mapping
import re, hashlib

_CITATION = re.compile("\\[S(\\d+)\\]")


def _sentences(text):
    """Exact sentence and paragraph spans; never reconstruct or invent text."""
    sections = list(re.finditer("(?m)^#{1,6}\\s+([^\\n]+)\\n?", text))
    boundaries = [
        (
            m.end(),
            sections[i + 1].start() if i + 1 < len(sections) else len(text),
            m.group(1).strip(),
        )
        for i, m in enumerate(sections)
    ]
    if not boundaries:
        boundaries = [(0, len(text), "document")]
    records = []
    for start, end, section in boundaries:
        for paragraph in re.finditer("\\S.*?(?=\\n[ \\t]*\\n|\\Z)", text[start:end], re.S):
            pstart = start + paragraph.start()
            pend = start + paragraph.end()
            while pend > pstart and text[pend - 1].isspace():
                pend -= 1
            for segment in re.finditer(
                "\\S.*?(?:[.!?](?=\\s+(?:[A-Z]|\\[)|$)|$)", text[pstart:pend], re.S
            ):
                left, right = (pstart + segment.start(), pstart + segment.end())
                while right > left and text[right - 1].isspace():
                    right -= 1
                quote = text[left:right]
                if quote:
                    records.append(
                        {
                            "quote": quote,
                            "span": [left, right],
                            "section": section,
                            "paragraph_span": [pstart, pend],
                        }
                    )
    return records


def _plain(value):
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _paragraphs(text):
    seen, records, indices = (set(), [], {})
    for sentence in _sentences(text):
        span = tuple(sentence["paragraph_span"])
        if span in seen:
            continue
        seen.add(span)
        section = sentence["section"]
        index = indices.get(section, 0)
        indices[section] = index + 1
        quote = text[span[0] : span[1]]
        records.append(
            {
                "section": section,
                "paragraph_index": index,
                "span": list(span),
                "quote": quote,
                "paragraph_sha256": _sha(quote),
            }
        )
    for item in records:
        item["section_paragraph_count"] = indices[item["section"]]
    return records


def _namespace(value):
    if isinstance(value, str):
        return _CITATION.sub(lambda match: "[HIST_S" + match.group(1) + "]", value)
    if isinstance(value, dict):
        return {key: _namespace(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_namespace(item) for item in value]
    return value
