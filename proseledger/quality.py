"""Explainable English style signals and conservative revision guardrails.

These rules do not estimate authorship, detect AI reliably, or establish semantic
equivalence. A zero style score is not a quality guarantee. The revision checks
cover digit-written numbers, S-number citations, and a few conspicuous changes
in claim strength; source verification and a separate semantic judge remain
necessary. In proposal mode, obvious claims of our own completed experiments
are flagged, while cited third-party findings are allowed.
"""

from __future__ import annotations
from collections import Counter
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from functools import lru_cache
import re

_WORD = re.compile("[A-Za-z]+(?:['’-][A-Za-z]+)*")
_CITATION_GROUP = re.compile("\\[\\s*S\\d+(?:\\s*[,;]\\s*S\\d+)*\\s*\\]", re.I)
_CITATION_KEY = re.compile("S\\d+", re.I)
_NUMBER = re.compile(
    "(?<![\\w.\\-])[+\\-]?(?:(?:\\d{1,3}(?:,\\d{3})+|\\d+)(?:\\.\\d+)?|\\.\\d+)(?:[eE][+\\-]?\\d{1,3})?(?:\\s*%)?(?!\\d|\\.\\d)"
)
_SCAFFOLDING = (
    "\\bit is (?:important|crucial|essential|worthwhile) to (?:note|mention|highlight) that\\b",
    "\\bit (?:is worth noting|should be noted) that\\b",
    "\\bin (?:today's|the current|the modern) (?:rapidly[ -](?:evolving|changing) )?landscape\\b",
    "\\bin the (?:ever[ -]evolving|rapidly[ -]evolving) (?:landscape|world|realm)\\b",
    "\\b(?:delve|delving) into\\b",
    "\\ba testament to\\b",
    "\\bpav(?:e|es|ing) the way for\\b",
    "\\bunlock(?:s|ing)? (?:the )?(?:full|true|vast|immense) potential\\b",
    "\\bplays? a (?:pivotal|crucial|vital) role in\\b",
    "\\b(?:in conclusion|to summarize|in summary),? (?:it is|it can be|we can)\\b",
)
_PROMOTIONAL = re.compile(
    "\\b(?:groundbreaking|revolutionary|game[ -]changing|unparalleled|unprecedented|remarkable|remarkably|transformative|seamless|seamlessly|cutting[ -]edge)\\b",
    re.I,
)
_HEDGES = {
    "may",
    "might",
    "could",
    "perhaps",
    "possibly",
    "potentially",
    "arguably",
    "presumably",
    "apparently",
    "seem",
    "seems",
    "appear",
    "appears",
}
_TENTATIVE = re.compile(
    "\\b(?:may|might|could|perhaps|possibly|potentially|tentative|hypothesi[sz](?:e|es|ed)|hypothesis|expect(?:s|ed)?|anticipat(?:e|es|ed)|aim(?:s)?|plan(?:s)?|intend(?:s)?)\\b",
    re.I,
)
_CERTAIN = re.compile(
    "\\b(?:prov(?:e|es|ed|en)|guarantee(?:s|d)?|confirm(?:s|ed)?|demonstrat(?:e|es|ed)|establish(?:es|ed)?|validat(?:e|es|ed))\\b",
    re.I,
)
_OWN = re.compile("\\b(?:we|our|ours)\\b", re.I)
_DIRECT_NEGATION = re.compile(
    "\\b(?:not|never|cannot|can't|doesn't|don't|didn't|isn't|aren't|wasn't|weren't|hasn't|haven't|won't|wouldn't|couldn't|shouldn't)(?:\\s+(?:yet|directly|conclusively|empirically|independently|necessarily|fully|reliably|alone|itself|be|been|have|by\\s+itself|on\\s+its\\s+own))*\\s*$",
    re.I,
)


def _affirmed_certainties(text):
    """Ignore a directly negated certainty verb, without ignoring its whole sentence."""
    return {
        match.group().lower()
        for match in _CERTAIN.finditer(text)
        if not _DIRECT_NEGATION.search(text[max(0, match.start() - 100) : match.start()])
    }


_FUTURE = re.compile(
    "\\b(?:will|would|may|might|could|plan(?:s|ned)?|aim(?:s)?|intend(?:s)?|expect(?:s|ed)?|hypothesi[sz](?:e|es)|propos(?:e|es))\\b",
    re.I,
)
_OWN_EMPIRICAL = (
    re.compile(
        "\\b(?:we|our\\s+(?:(?:proposed|new)\\s+)?(?:method|model|system|approach|framework|agent|pipeline))\\b[^.!?]{0,90}\\b(?:achiev(?:e|es|ed)|outperform(?:s|ed)?|obtain(?:s|ed)?|measur(?:e|es|ed)|observ(?:e|es|ed)|record(?:s|ed)?)\\b",
        re.I,
    ),
    re.compile(
        "\\bour\\s+(?:experiments?|results?|evaluations?|measurements?|ablation(?:s| study)?)\\b[^.!?]{0,50}\\b(?:show(?:s|ed)?|demonstrat(?:e|es|ed)|confirm(?:s|ed)?|reveal(?:s|ed)?|indicat(?:e|es|ed)|prov(?:e|es|ed)|establish(?:es|ed)?)\\b",
        re.I,
    ),
    re.compile(
        "\\bwe\\s+(?:conducted|ran|performed|completed)\\b[^.!?]{0,60}\\b(?:experiments?|benchmarks?|evaluations?|ablations?|trials?)\\b",
        re.I,
    ),
    re.compile(
        "\\bwe\\s+(?:evaluated|tested|trained)\\b[^.!?]{0,60}\\b(?:models?|systems?|agents?|datasets?|benchmarks?)\\b",
        re.I,
    ),
)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split("(?<=[.!?])\\s+(?=[A-Z\\[])|\\n+", text) if s.strip()]


def _citation_keys(text: str) -> set[str]:
    return {
        key.upper()
        for group in _CITATION_GROUP.findall(text)
        for key in _CITATION_KEY.findall(group)
    }


def _numbers(text: str) -> set[str]:
    values = set()
    text = _CITATION_GROUP.sub("", text).replace("−", "-")
    text = re.sub("(?<=\\d)\\s*[-–—]\\s*(?=\\d)", " ", text)
    for match in _NUMBER.finditer(text):
        raw = re.sub("\\s+", "", match.group()).replace(",", "")
        percent = raw.endswith("%")
        try:
            numeric = format(Decimal(raw.rstrip("%")).normalize(), "f")
        except InvalidOperation:
            numeric = raw.rstrip("%")
        if numeric == "-0":
            numeric = "0"
        values.add(numeric + ("%" if percent else ""))
    return values


def _is_cited_third_party(sentence: str) -> bool:
    attribution = re.search(
        "\\b(?:prior|previous|published|earlier|existing|baseline|et\\s+al)\\b", sentence, re.I
    )
    return bool(_citation_keys(sentence) and attribution) and (not _OWN.search(sentence))


def score_text(text: str) -> dict:
    """Return a 0--100 style heuristic (lower is fewer flagged signals).

    The score is an interpretable weighted count, normalized toward 250 words;
    it is neither an AI probability nor an assessment of scientific validity.
    Features and issue fragments make every contributing rule inspectable.
    """
    text = text or ""
    text = re.split("(?im)^#{1,6}\\s+(?:references|bibliography|supplied sources)\\s*$", text)[0]
    text = re.sub("(?m)^\\s*#{1,6}\\s+.*$", "", text)
    text = re.sub("\\[[^\\]\\n]+\\](?:\\([^\\n)]+\\))?", "", text)
    words = _WORD.findall(text)
    sentences = _sentences(text)
    issues = []
    counts = Counter()

    def add(kind: str, message: str, fragment: str) -> None:
        counts[kind] += 1
        issues.append({"kind": kind, "message": message, "fragment": fragment})

    for pattern in _SCAFFOLDING:
        for match in re.finditer(pattern, text, re.I):
            add(
                "scaffolding",
                "Consider replacing generic framing with the specific point.",
                match.group(),
            )
    for match in _PROMOTIONAL.finditer(text):
        add(
            "promotional",
            "Check whether this promotional wording has concrete support.",
            match.group(),
        )
    for sentence in sentences:
        tokens = list(_WORD.finditer(sentence))
        hedge_positions = [i for i, token in enumerate(tokens) if token.group().lower() in _HEDGES]
        consumed_until = -1
        for position in hedge_positions:
            if position <= consumed_until:
                continue
            nearby = [p for p in hedge_positions if position <= p <= position + 7]
            if len(nearby) >= 3:
                end = nearby[-1]
                add(
                    "hedge_stacking",
                    "Several uncertainty markers overlap; retain the necessary qualification.",
                    sentence[tokens[position].start() : tokens[end].end()],
                )
                consumed_until = end
    normalized_sentences = [" ".join(_WORD.findall(s.lower())) for s in sentences]
    repeated_sentences = {
        sentence: count
        for sentence, count in Counter(normalized_sentences).items()
        if count > 1 and len(sentence.split()) >= 6
    }
    for sentence, count in repeated_sentences.items():
        add(
            "repetition",
            f"This sentence occurs {count} times; check whether repetition is useful.",
            sentence,
        )
    lower_words = [word.lower() for word in words]
    ngrams = Counter((tuple(lower_words[i : i + 5]) for i in range(max(0, len(lower_words) - 4))))
    selected_phrases = []
    for ngram, count in ngrams.most_common():
        phrase = " ".join(ngram)
        if count < 3 or any((phrase in sentence for sentence in repeated_sentences)):
            continue
        if any((len(set(ngram) & set(previous)) >= 4 for previous in selected_phrases)):
            continue
        add(
            "repetition",
            f"This five-word phrase occurs {count} times; check for formulaic repetition.",
            phrase,
        )
        selected_phrases.append(ngram)
        if len(selected_phrases) == 3:
            break
    templates = (
        "\\bnot only\\b[^.!?\\n]{0,100}\\bbut also\\b",
        "(?:^|[.!?]\\s+)(?:this (?:highlights|underscores)|it is evident)\\b",
    )
    for template in templates:
        hits = list(re.finditer(template, text, re.I))
        if len(hits) >= 3:
            add(
                "symmetry",
                "The same rhetorical frame occurs at least three times; check its purpose, without forcing varied sentence lengths.",
                hits[0].group().strip(),
            )
    weights = {
        "scaffolding": 8,
        "promotional": 5,
        "hedge_stacking": 9,
        "repetition": 10,
        "symmetry": 5,
    }
    raw = sum((counts[kind] * weight for kind, weight in weights.items()))
    normalization = 250 / max(250, len(words))
    score = min(100, round(raw * normalization))
    if not text.strip():
        add("empty", "There is no text to assess.", "")
        score = 100
    band = (
        "few flagged signals"
        if score < 15
        else "some flagged signals" if score < 35 else "many flagged signals"
    )
    if not text.strip():
        band = "empty text"
    return {
        "score": score,
        "features": {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "scaffolding_count": counts["scaffolding"],
            "promotional_count": counts["promotional"],
            "hedge_stacking_count": counts["hedge_stacking"],
            "repetition_count": counts["repetition"],
            "symmetry_count": counts["symmetry"],
            "weighted_count": raw,
            "length_normalization": round(normalization, 4),
            "weights": weights,
            "scope": "English style heuristic; not authorship probability or scientific quality.",
        },
        "issues": issues,
        "label": f"{band}; heuristic only, not authorship probability",
    }


def citation_keys(text: str) -> set[str]:
    """Extract the same citation syntax used by the revision guardrail."""
    return _citation_keys(text)


def check_revision(
    original: str, candidate: str, allowed_citation_keys: list[str], proposal_mode: bool = True
) -> dict:
    """Flag surface-level fidelity violations; passing is not semantic proof.

    Numeric sets ignore formatting and repeated occurrences, but preserve a
    percent sign. Citation checks support [S1] and [S1, S2]. Claim checks are
    deliberately narrow; an API or human judge must check meaning, attribution,
    units, and entailment. No score improvement is required or assumed.
    """
    issues = []
    if not candidate or not candidate.strip():
        return {"passed": False, "issues": ["Empty revision: no candidate text was produced."]}
    original = original or ""
    before_words = len(_WORD.findall(original))
    after_words = len(_WORD.findall(candidate))
    if before_words >= 20 and after_words < before_words * 0.5:
        issues.append(
            f"Large deletion: word count fell from {before_words} to {after_words} (over 50%)."
        )
    before_numbers, after_numbers = (_numbers(original), _numbers(candidate))
    if after_numbers - before_numbers:
        issues.append(
            "New or changed numeric values: "
            + ", ".join(sorted(after_numbers - before_numbers))
            + "."
        )
    if before_numbers - after_numbers:
        issues.append(
            "Missing original numeric values: "
            + ", ".join(sorted(before_numbers - after_numbers))
            + "."
        )
    allowed = {key.strip().strip("[]").upper() for key in allowed_citation_keys}
    before_citations, after_citations = (_citation_keys(original), _citation_keys(candidate))
    if after_citations - allowed:
        issues.append(
            "Unknown citation keys: " + ", ".join(sorted(after_citations - allowed)) + "."
        )
    if before_citations - after_citations:
        issues.append(
            "Missing original citation keys: "
            + ", ".join(sorted(before_citations - after_citations))
            + "."
        )
    original_certainties = {m.group().lower() for m in _CERTAIN.finditer(original)}
    if _TENTATIVE.search(original):
        for sentence in _sentences(candidate):
            new_certainties = {
                m.group().lower() for m in _CERTAIN.finditer(sentence)
            } - original_certainties
            if (
                new_certainties
                and (not _TENTATIVE.search(sentence))
                and (not _is_cited_third_party(sentence))
            ):
                issues.append(
                    "Possible claim strengthening: tentative source text now uses "
                    + ", ".join(sorted(new_certainties))
                    + ": "
                    + sentence[:200]
                )
                break
    if proposal_mode:
        for sentence in _sentences(candidate):
            if _FUTURE.search(sentence) or _is_cited_third_party(sentence):
                continue
            if any((pattern.search(sentence) for pattern in _OWN_EMPIRICAL)):
                issues.append(
                    "Proposal-mode empirical claim: wording implies our own completed measurements or experiments; check evidence: "
                    + sentence[:200]
                )
                break
    return {"passed": not issues, "issues": issues}


_SMALL_NUMBERS = dict(
    zip(
        "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split(),
        range(20),
    )
)
_TENS = dict(
    zip("twenty thirty forty fifty sixty seventy eighty ninety".split(), range(20, 100, 10))
)
_NUMBER_WORDS = re.compile(
    "\\b(?:"
    + "|".join(_TENS)
    + ")(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?\\b|\\b(?:"
    + "|".join(_SMALL_NUMBERS)
    + ")\\b",
    re.I,
)
_EXPERIMENT_SUBJECT = "(?:experiments?|evaluations?|measurements?|trials?|benchmarks?)"
_EXPERIMENT_MODIFIERS = "(?:(?!(?:but|and|or|while|whereas|although|however|yet|fewer|less|more)\\b)[A-Za-z-]+\\s+){0,4}"
_PENDING_EXPERIMENT = re.compile(
    "\\bno\\s+"
    + _EXPERIMENT_MODIFIERS
    + _EXPERIMENT_SUBJECT
    + "\\s+(?:(?:were|have been|have yet been|are|was|has been|is)\\s+)?(?:conducted|run|performed|completed)\\b|\\b(?:have\\s+|has\\s+|were\\s+|was\\s+|are\\s+|did\\s+)?not\\s+(?:yet\\s+)?(?:conducted?|run|performed|completed|evaluated|tested|measured)\\b|\\b(?:experiments?|evaluations?|measurements?)\\b[^.!?\\n]{0,35}\\b(?:remain(?:s)?|are|is)\\s+(?:planned|pending|future work|not yet)\\b|\\b(?:experiments?|evaluations?|measurements?)\\b[^.!?\\n]{0,30}\\bnot\\s+(?:yet\\s+)?(?:been\\s+)?(?:conducted|run|performed|completed)\\b|\\b"
    + _EXPERIMENT_SUBJECT
    + "\\s+(?:(?:remain(?:s)?|are|is)\\s+(?:still\\s+)?(?:unperformed|pending|to\\s+be\\s+(?:conducted|performed|completed|run))|(?:have|has)\\s+yet\\s+to\\s+be\\s+(?:conducted|performed|completed|run))\\b",
    re.I,
)
_PROPOSAL = re.compile(
    "\\b(?:propos(?:e|ed|al)|hypothesis|hypothesi[sz]e|planned|will evaluate|future work|plan(?:s)?\\s+to|intend(?:s)?\\s+to)\\b",
    re.I,
)
_DOMAIN_TERMS = (
    "retrieval augmented generation",
    "supervised fine tuning",
    "human evaluation",
    "held out",
    "baseline",
    "ablation",
)


def _citation_identities(text: str) -> set[str]:
    citations = set()
    for group in re.findall("\\[([^\\]\\n]+)\\]", text):
        if re.fullmatch("\\s*S\\d+(?:\\s*[,;|]\\s*S\\d+)*\\s*", group, re.I):
            citations.update((key.upper() for key in _CITATION_KEY.findall(group)))
        elif re.fullmatch("\\s*\\d+(?:\\s*[,;]\\s*\\d+)*\\s*", group):
            citations.update(("numeric-ref:" + key for key in re.findall("\\d+", group)))
        elif len(group.strip()) >= 12 and re.search("[A-Za-z]", group) and (" " in group):
            citations.update(
                ("title:" + " ".join(title.casefold().split()) for title in group.split("|"))
            )
    return citations


def _fact_text(text: str) -> str:
    text = re.sub("https?://\\S+", "", text)

    def without_citation(match):
        return "" if _citation_identities(match.group()) else match.group()

    text = re.sub("\\[[^\\]\\n]+\\]", without_citation, text)
    text = re.sub("(?m)^(\\s*#{1,6}\\s+)\\d+(?:\\.\\d+)*[.)]?\\s+(?=[A-Za-z])", "\\1", text)
    text = re.sub("(?m)^(\\s*)(?:\\d+(?:\\.\\d+)*[.)]|\\(\\d+\\))\\s+(?=[A-Za-z])", "\\1", text)
    return text.replace("−", "-")


def _numeric_text(text: str) -> str:
    text = _fact_text(text)
    text = re.sub("\\ba\\s+single(?=\\s+[A-Za-z])\\b", "one", text, flags=re.I)

    def replace_number_word(match):
        word = match.group().casefold()
        if word == "one":
            prefix = text[max(0, match.start() - 70) : match.start()]
            tail = text[match.end() :]
            numeric_partitive = re.match(
                "\\s+of\\s+(?:(?:the|these|those|our)\\s+)?(?:[0-9]+|"
                + "|".join((*_SMALL_NUMBERS, *_TENS))
                + ")\\b",
                tail,
                re.I,
            )
            idiom = re.match("\\s+another\\b", tail, re.I) or (
                re.match("\\s+of\\b", tail, re.I) and (not numeric_partitive)
            )
            reference_prefix = re.search(
                "\\b(?:each|every|this|that|the|another|either|a|an)\\s+(?:(?:new|old|previous|next|same|different|alternative|existing|earlier|later|other|better|worse|revised|original|remaining|similar)\\s+){0,3}$",
                prefix,
                re.I,
            )
            reference_tail = re.match(
                "(?:\\s*(?:$|[.,;:!?]))|(?:\\s+(?:to|with|in|on|for|from|as|by|at|through|and|or|but|that|which|is|was|has|had|will|can|could|must|should|would|may|might)\\b)",
                tail,
                re.I,
            )
            generic_subject = re.match(
                "\\s+(?:can|could|should|would|may|might|must)\\s+[A-Za-z]", tail, re.I
            )
            if idiom or (reference_prefix and reference_tail) or generic_subject:
                return word
        parts = re.split("[- ]", word)
        return str(sum((_SMALL_NUMBERS.get(p, _TENS.get(p, 0)) for p in parts)))

    text = _NUMBER_WORDS.sub(replace_number_word, text)
    text = re.sub(
        "\\b(\\d+)\\s+(hundred|thousand)\\b",
        lambda m: str(int(m[1]) * (100 if m[2] == "hundred" else 1000)),
        text,
        flags=re.I,
    )
    return re.sub("(?<=\\d)\\s+percent\\b", "%", text, flags=re.I)


def _numeric_units(text: str) -> set[str]:
    normalized = _numeric_text(text)
    units = {
        "round": "round",
        "iteration": "round",
        "rater": "participant",
        "reviewer": "participant",
        "participant": "participant",
        "person": "participant",
        "people": "participant",
        "second": "second",
        "minute": "minute",
        "hour": "hour",
        "day": "day",
        "week": "week",
        "sample": "sample",
        "paper": "paper",
        "source": "source",
        "paragraph": "paragraph",
        "token": "token",
        "model": "model",
        "gpu": "gpu",
        "parameter": "parameter",
        "gb": "gb",
        "gigabyte": "gb",
        "mb": "mb",
        "megabyte": "mb",
        "tb": "tb",
        "terabyte": "tb",
    }
    pattern = re.compile("(" + _NUMBER.pattern + ")\\s*(" + "|".join(units) + ")s?\\b", re.I)
    found = set()
    for match in pattern.finditer(normalized):
        number = next(iter(_numbers(match[1])), match[1])
        found.add(number + " " + units[match[2].lower()])
    return found


def _metric_values(text: str) -> set[str]:
    text = _numeric_text(text)
    metrics = "accuracy|precision|recall|f1|auroc|auc|latency|cost"
    before = re.compile(
        "\\b("
        + metrics
        + ")\\b(?:\\s+(?:of|was|is|equals?|at|measured|reached)|\\s*[:=])*\\s*("
        + _NUMBER.pattern
        + ")",
        re.I,
    )
    after = re.compile("(" + _NUMBER.pattern + ")\\s+(" + metrics + ")\\b", re.I)
    pairs = [(m[1].lower(), m[2]) for m in before.finditer(text)]
    pairs += [(m[2].lower(), m[1]) for m in after.finditer(text)]
    return {metric + "=" + next(iter(_numbers(number)), number) for metric, number in pairs}


def _normal_terms(text: str) -> str:
    text = re.sub("(?<=\\d)(?=(?:GB|MB|TB)\\b)", " ", text, flags=re.I)
    return " " + " ".join(re.findall("[A-Za-z0-9]+", text.lower())) + " "


_CLAUSE_BOUNDARY = re.compile(
    "(?<=[.!?])\\s+(?=[A-Z\\[])|\\n+|;\\s*|\\s*\\b(?:but|whereas|while|although)\\b\\s*|,\\s*yet\\s+|(?:,\\s*)?\\band\\s+(?=(?:we|our|the\\s+(?:results|experiments|evaluation))\\b)|,\\s+(?=(?:we|our)\\b)",
    re.I,
)
_NEGATION_WORD = re.compile(
    "\\b(?:not(?!\\s+(?:only|just|merely)\\b)|none|never|cannot|can't|doesn't|don't|didn't|isn't|aren't|wasn't|weren't|hasn't|haven't|won't|wouldn't|couldn't|shouldn't|no)\\b",
    re.I,
)
_EMPIRICAL_VERB = re.compile(
    "\\b(?:achiev(?:e|es|ed)|outperform(?:s|ed)?|obtain(?:s|ed)?|measur(?:e|es|ed)|observ(?:e|es|ed)|record(?:s|ed)?|conducted|ran|performed|completed|evaluated|tested|trained|show(?:s|ed)?|demonstrat(?:e|es|ed)|confirm(?:s|ed)?|reveal(?:s|ed)?|indicat(?:e|es|ed)|prov(?:e|es|ed)|establish(?:es|ed)?|validat(?:e|es|ed))\\b",
    re.I,
)
_PAST_EMPIRICAL = re.compile(
    "\\b(?:achieved|outperformed|obtained|measured|observed|recorded|conducted|ran|performed|completed|evaluated|tested|trained|showed|demonstrated|confirmed|revealed|indicated|proved|proven|established|validated)\\b",
    re.I,
)
_CLAIM_STOP = set(
    "a an the this that these those we our it is are was were be been being do does did has have had not no never to of in on for by as and but may might could would will can should must plan plans planned propose proposed yet already".split()
)


@lru_cache(maxsize=32)
def _clause_spans(text: str) -> list[tuple[str, int, int]]:
    spans, cursor = ([], 0)
    for boundary in list(_CLAUSE_BOUNDARY.finditer(text)) + [None]:
        end = boundary.start() if boundary else len(text)
        raw = text[cursor:end]
        start = cursor + len(raw) - len(raw.lstrip())
        stop = end - len(raw) + len(raw.rstrip())
        if start < stop:
            spans.append((text[start:stop], start, stop))
        cursor = boundary.end() if boundary else len(text)
    return spans


def _claim_tokens(text: str) -> set[str]:
    words = _WORD.findall(text.lower().replace("’", "'"))
    tokens = set()
    for word in words:
        if word in _CLAIM_STOP or word.endswith("n't"):
            continue
        if word.endswith("ed") and len(word) > 5:
            word = word[:-2]
        elif word.endswith("s") and len(word) > 4:
            word = word[:-1]
        tokens.add(word.rstrip("e") if len(word) > 4 else word)
    return tokens


def _aligned_clause(quote: str, other: str) -> tuple[str, int, int] | None:
    """Locate evidence in the other draft, never an arbitrary first edit."""
    exact = other.find(quote) if quote else -1
    if exact >= 0:
        return (quote, exact, exact + len(quote))
    target = _claim_tokens(quote)
    scored = []
    for clause, start, end in _clause_spans(other):
        terms = _claim_tokens(clause)
        overlap = len(target & terms) / max(1, len(target | terms))
        literal = SequenceMatcher(None, quote.casefold(), clause.casefold()).ratio()
        scored.append((0.8 * overlap + 0.2 * literal, clause, start, end))
    if not scored:
        return None
    score, clause, start, end = max(scored)
    return (clause, start, end) if score >= 0.25 else None


_ADEQUACY_COPULA = re.compile(
    "^\\s*(?P<subject>[^:;,.!?]{1,90}?)\\s+(?:is|are|was|were|remains?)\\s+(?P<negation>not\\s+)?(?P<adjective>insufficient|inadequate|sufficient|adequate|enough)\\b",
    re.I,
)
_ADEQUACY_ACTION = re.compile(
    "^\\s*(?P<subject>[^:;,.!?]{1,90}?)\\s+(?P<operator>cannot|can't|can\\s+not|does\\s+not|do\\s+not|did\\s+not|could\\s+not|can|could|does|do|did|fails?\\s+to)\\s+(?:fully\\s+)?(?:meet|satisfy)\\s+(?:(?:this|that|the|these|those|our|its)\\s+)?(?:requirements?|criteria|criterion|conditions?|needs?|goals?|objectives?)\\b",
    re.I,
)


def _adequacy_frame(text: str):
    """Return the subject and polarity of a locally expressed adequacy claim."""
    if match := _ADEQUACY_COPULA.match(text):
        negative = match["adjective"].lower() in {"insufficient", "inadequate"}
        if match["negation"]:
            negative = not negative
        return {
            "subject": _claim_tokens(match["subject"]),
            "negative": negative,
            "quote": text[: match.end()],
        }
    if match := _ADEQUACY_ACTION.match(text):
        negative = bool(re.search("cannot|can't|\\bnot\\b|fails?\\s+to", match["operator"], re.I))
        return {
            "subject": _claim_tokens(match["subject"]),
            "negative": negative,
            "quote": text[: match.end()],
        }
    return None


def _negation_scopes(text: str):
    """Exclude explanatory tails after a colon from polarity alignment."""
    spans = []
    for clause, start, _ in _clause_spans(text):
        cursor = 0
        for piece in re.split(":\\s*", clause):
            offset = clause.find(piece, cursor)
            cursor = offset + len(piece)
            stripped = piece.strip()
            if stripped:
                first = start + offset + len(piece) - len(piece.lstrip())
                spans.append((stripped, first, first + len(stripped)))
    return spans


def _align_negation_scope(quote: str, other: str):
    before_frame = _adequacy_frame(quote)
    target = _claim_tokens(quote)
    candidates = []
    for clause, start, end in _negation_scopes(other):
        after_frame = _adequacy_frame(clause)
        if (
            before_frame
            and after_frame
            and before_frame["subject"]
            and (before_frame["subject"] == after_frame["subject"])
        ):
            score = 2.0
        else:
            terms = _claim_tokens(clause)
            score = (
                0.8 * len(target & terms) / max(1, len(target | terms))
                + 0.2 * SequenceMatcher(None, quote.casefold(), clause.casefold()).ratio()
            )
        candidates.append((score, clause, start, end))
    if not candidates:
        return None
    score, clause, start, end = max(candidates)
    return (clause, start, end) if score >= 0.25 else None


def _nonassertive_at(clause: str, verb_start: int) -> bool:
    """Recognize explicit scope immediately preceding a verb, not distant plans."""
    prefix = clause[:verb_start]
    prefix = re.sub(
        ",\\s*(?:however|nevertheless|therefore|in\\s+fact|at\\s+present)\\s*,",
        " ",
        prefix,
        flags=re.I,
    )
    if _DIRECT_NEGATION.search(prefix[-120:]):
        return True
    if re.search(
        "\\bno\\s+"
        + _EXPERIMENT_MODIFIERS
        + _EXPERIMENT_SUBJECT
        + "\\s+(?:(?:have|has)\\s+been|were|was|are|is)\\s+(?:yet\\s+)?$",
        prefix,
        re.I,
    ):
        return True
    if re.search(
        "\\b(?:remain(?:s)?|(?:have|has|is|are)\\s+yet)\\s+to\\s+(?:be\\s+)?(?:(?:empirically|independently|fully|conclusively|rigorously)\\s+){0,2}$",
        prefix,
        re.I,
    ):
        return True
    if re.search(
        "\\bnot\\s+(?:(?:empirical|verified|observed|scientific|conclusive)\\s+){0,2}(?:findings?|results?|evidence|facts?)\\s+(?:that\\s+(?:have|has)\\s+been\\s+)?$",
        prefix,
        re.I,
    ):
        return True
    if re.search("\\b(?:neither|nor)\\b[^,;.!?]{0,100}$", prefix, re.I):
        return True
    if re.search("\\bwithout\\s+(?:(?:having|ever|yet)\\s+){0,3}$", prefix, re.I):
        return True
    if re.search(
        "\\b(?:will|would|may|might|could|can|should|must)\\s+(?:[A-Za-z-]+\\s+){0,6}$",
        prefix,
        re.I,
    ):
        return True
    verb = _EMPIRICAL_VERB.match(clause, verb_start)
    if (
        verb
        and verb.group().lower() in {"record", "records", "measure", "measures"}
        and re.search("\\bpropos(?:e|es|ed)\\b[^,;.!?]{0,150}$", prefix, re.I)
        and (not re.search("\\band\\s*$", prefix, re.I))
    ):
        return True
    if re.search(
        "\\b(?:plan(?:s|ned)?|aim(?:s)?|intend(?:s)?|expect(?:s|ed)?|hope(?:s)?)\\s+(?:[A-Za-z-]+\\s+){0,3}to\\s+(?:[A-Za-z-]+\\s+){0,3}$",
        prefix,
        re.I,
    ):
        return True
    return bool(re.search("\\b(?:if|unless|whether)\\b[^,;.!?]{0,100}$", prefix, re.I))


def _asserted_certainty_matches(clause: str):

    def negative_object(match):
        return bool(
            re.match(
                "\\s+(?:(?:currently|yet|actually|directly|necessarily|conclusively)\\s+){0,2}(?:neither\\b|nothing\\b|no\\b(?!\\s+(?:fewer|less)\\b))",
                clause[match.end() :],
                re.I,
            )
        )

    return [
        match
        for match in _CERTAIN.finditer(clause)
        if not _nonassertive_at(clause, match.start()) and (not negative_object(match))
    ]


def guard_rewrite(original: str, candidate: str, protected_terms: list[str] | None = None) -> dict:
    """Conservative surface checks, shared by all rewrite branches.

    ``findings`` carry exact evidence quotes/spans for localized memory admission.
    Hard findings establish a deterministic surface mismatch, not factual truth.
    Suspected findings are ambiguous lexical concerns: they conservatively block
    this candidate but must not automatically become active failure memories.
    Passing is not proof of entailment, factual correctness, or semantic identity.
    """
    original, candidate = (original or "", candidate or "")
    issues, findings = ([], [])
    identity_unchanged = bool(candidate.strip()) and original == candidate

    def add(kind, reason, before_quote="", after_quote="", severity="hard"):
        if identity_unchanged:
            return
        issues.append(reason)
        before_start = original.find(before_quote) if before_quote else -1
        after_start = candidate.find(after_quote) if after_quote else -1
        findings.append(
            {
                "kind": kind,
                "severity": severity,
                "verified": severity == "hard",
                "finding_id": f"surface-{len(findings) + 1:03d}",
                "requires_semantic_review": severity == "suspected",
                "evidence_type": "surface_mismatch" if severity == "hard" else "lexical_concern",
                "reason": reason,
                "before_quote": before_quote,
                "after_quote": after_quote,
                "before_span": (
                    [before_start, before_start + len(before_quote)] if before_start >= 0 else None
                ),
                "after_span": (
                    [after_start, after_start + len(after_quote)] if after_start >= 0 else None
                ),
                "verification_scope": (
                    "Deterministic surface evidence; not semantic or factual proof."
                    if severity == "hard"
                    else "Unverified lexical concern with exact quotes; not semantic or factual proof."
                ),
            }
        )

    def quotes_for_change(extractor, changed, text, other, is_after):
        found = next(
            (clause for clause, _, _ in _clause_spans(text) if extractor(clause) & changed), ""
        )
        aligned = _aligned_clause(found, other) if found else None
        paired = aligned[0] if aligned else ""
        return (paired, found) if is_after else (found, paired)

    before_words, after_words = (len(_WORD.findall(original)), len(_WORD.findall(candidate)))
    number_values = lambda value: _numbers(_numeric_text(value))
    before_numbers, after_numbers = (number_values(original), number_values(candidate))
    before_cites, after_cites = (_citation_identities(original), _citation_identities(candidate))
    before_units, after_units = (_numeric_units(original), _numeric_units(candidate))
    before_metrics, after_metrics = (_metric_values(original), _metric_values(candidate))
    terms = set(protected_terms or [])
    clean_original = _fact_text(original)
    terms.update(re.findall("\\b[A-Z][A-Z0-9]{1,}\\b", clean_original))
    terms.difference_update({"S1", "S2", "S3", "S4", "S5", "S6", "REF"})
    terms.update(re.findall("`([^`\\n]+)`", original))
    before_normal, after_normal = (_normal_terms(original), _normal_terms(candidate))
    terms.update((term for term in _DOMAIN_TERMS if _normal_terms(term) in before_normal))
    aliases = {
        "LLM": ("large language model", "large language models"),
        "LLMs": ("large language model", "large language models"),
        "AI": ("artificial intelligence",),
        "SFT": ("supervised fine tuning",),
        "RAG": ("retrieval augmented generation",),
        "API": ("application programming interface",),
        "GB": ("gigabyte", "gigabytes"),
        "MB": ("megabyte", "megabytes"),
        "TB": ("terabyte", "terabytes"),
    }
    missing_terms = [
        term
        for term in sorted(terms)
        if not any(
            (_normal_terms(variant) in after_normal for variant in (term, *aliases.get(term, ())))
        )
    ]
    if not candidate.strip():
        add("empty", "Empty revision: no candidate text was produced.", original[:350])
    if before_words >= 10 and after_words < before_words * 0.5:
        add(
            "large_deletion",
            f"Large deletion: word count fell from {before_words} to {after_words} (over 50%).",
            original[:350],
            candidate[:350],
            "suspected",
        )
    for kind, label, values, extractor, is_after in (
        (
            "numeric_values",
            "New or changed numeric values",
            after_numbers - before_numbers,
            number_values,
            True,
        ),
        (
            "numeric_values",
            "Missing original numeric values",
            before_numbers - after_numbers,
            number_values,
            False,
        ),
        (
            "quantities_units",
            "New or changed quantities/units",
            after_units - before_units,
            _numeric_units,
            True,
        ),
        (
            "quantities_units",
            "Missing original quantities/units",
            before_units - after_units,
            _numeric_units,
            False,
        ),
        (
            "metric_values",
            "New or changed metric/value pairs",
            after_metrics - before_metrics,
            _metric_values,
            True,
        ),
        (
            "metric_values",
            "Missing original metric/value pairs",
            before_metrics - after_metrics,
            _metric_values,
            False,
        ),
        (
            "citations",
            "New citation identities",
            after_cites - before_cites,
            _citation_identities,
            True,
        ),
        (
            "citations",
            "Missing original citation identities",
            before_cites - after_cites,
            _citation_identities,
            False,
        ),
    ):
        if values:
            text, other = (candidate, original) if is_after else (original, candidate)
            before_quote, after_quote = quotes_for_change(extractor, values, text, other, is_after)
            severity = "hard"
            if kind == "numeric_values":
                opposite = (
                    before_numbers - after_numbers if is_after else after_numbers - before_numbers
                )
                unit_bound = {pair.split(" ", 1)[0] for pair in before_units | after_units}
                metric_bound = {pair.split("=", 1)[1] for pair in before_metrics | after_metrics}
                word_only = number_values(text) - _numbers(_fact_text(text))
                if (
                    not opposite
                    and values <= word_only
                    and (not values & (unit_bound | metric_bound))
                ):
                    severity = "suspected"
            elif kind == "quantities_units":
                opposite = before_units - after_units if is_after else after_units - before_units
                if not opposite:
                    severity = "suspected"
            add(kind, label + ": " + ", ".join(sorted(values)), before_quote, after_quote, severity)
    if missing_terms:
        for term in missing_terms:
            before_quote = next(
                (
                    clause
                    for clause, _, _ in _clause_spans(original)
                    if _normal_terms(term) in _normal_terms(clause)
                ),
                "",
            )
            aligned = _aligned_clause(before_quote, candidate)
            add(
                "protected_terms",
                "Missing protected technical terms: " + term,
                before_quote,
                aligned[0] if aligned else "",
                "suspected",
            )
    pending_before = bool(_PENDING_EXPERIMENT.search(original))
    pending_after = bool(_PENDING_EXPERIMENT.search(candidate))
    if pending_before and (not pending_after):
        before_quote = next(
            (
                clause
                for clause, _, _ in _clause_spans(original)
                if _PENDING_EXPERIMENT.search(clause)
            ),
            "",
        )
        aligned = _aligned_clause(before_quote, candidate)
        add(
            "proposal_status",
            "The explicit statement that experiments/evaluation remain unperformed was removed.",
            before_quote,
            aligned[0] if aligned else "",
            "suspected",
        )
    negation_after_spans = set()
    for before_clause, _, _ in _negation_scopes(original):
        before_frame = _adequacy_frame(before_clause)
        if not _NEGATION_WORD.search(before_clause) and (
            not (before_frame and before_frame["negative"])
        ):
            continue
        aligned = _align_negation_scope(before_clause, candidate)
        if not aligned:
            continue
        after_clause, start, end = aligned
        after_frame = _adequacy_frame(after_clause)
        matched_frame = (
            before_frame
            and after_frame
            and before_frame["subject"]
            and (before_frame["subject"] == after_frame["subject"])
        )
        if matched_frame:
            if before_frame["negative"] == after_frame["negative"]:
                continue
            if before_frame["negative"]:
                add(
                    "negation",
                    "Possible strengthening through reversed adequacy polarity: "
                    + after_frame["quote"],
                    before_frame["quote"],
                    after_frame["quote"],
                    "hard",
                )
                negation_after_spans.add((start, end))
                continue
        before_tokens, after_tokens = (_claim_tokens(before_clause), _claim_tokens(after_clause))
        similarity = len(before_tokens & after_tokens) / max(1, len(before_tokens | after_tokens))
        if (
            similarity >= 0.75
            and len(before_tokens & after_tokens) >= 2
            and (not _NEGATION_WORD.search(after_clause))
        ):
            exact_predicate = before_tokens == after_tokens
            uncertain = bool(_FUTURE.search(after_clause)) or not exact_predicate
            add(
                "negation",
                "Possible strengthening through removed negation: " + after_clause[:200],
                before_clause,
                after_clause,
                "suspected" if uncertain else "hard",
            )
            negation_after_spans.add((start, end))
    proposal_mode = pending_before or bool(_PROPOSAL.search(original))
    original_clauses = {
        " ".join(clause.casefold().split()) for clause, _, _ in _clause_spans(original)
    }
    for clause, start, end in _clause_spans(candidate):
        if " ".join(clause.casefold().split()) in original_clauses:
            continue
        attributed = bool(_citation_identities(clause)) and (not _OWN.search(clause))
        if attributed:
            continue
        asserted_certainty = _asserted_certainty_matches(clause)
        possible_empirical = proposal_mode and bool(_EMPIRICAL_VERB.search(clause))
        if not asserted_certainty and (not possible_empirical):
            continue
        aligned = _aligned_clause(clause, original)
        before_clause = aligned[0] if aligned else ""
        if proposal_mode:
            own_result = any((pattern.search(clause) for pattern in _OWN_EMPIRICAL))
            passive_result = re.search(
                "\\b(?:experiments?|evaluations?)\\s+(?:were|have been)\\s+(?:conducted|completed|performed|run)\\b",
                clause,
                re.I,
            )
            own_past = bool(_OWN.search(clause) and _PAST_EMPIRICAL.search(clause))
            verbs = [
                m
                for m in _EMPIRICAL_VERB.finditer(clause)
                if not _nonassertive_at(clause, m.start())
            ]
            if (
                (own_result or passive_result or own_past)
                and verbs
                and (not _PENDING_EXPERIMENT.search(clause))
            ):
                concrete = (
                    any((_PAST_EMPIRICAL.fullmatch(m.group()) for m in verbs))
                    or bool(
                        re.search(
                            "\\bour\\s+(?:experiments?|results?|evaluations?|measurements?)\\b",
                            clause,
                            re.I,
                        )
                    )
                    or bool(passive_result)
                )
                add(
                    "proposal_status",
                    "Proposal status changed to completed empirical work: " + clause[:200],
                    before_clause,
                    clause,
                    "hard" if concrete else "suspected",
                )
        if _TENTATIVE.search(original) and (start, end) not in negation_after_spans:
            before_certain = {m.group().lower() for m in _asserted_certainty_matches(before_clause)}
            new_certain = {m.group().lower() for m in asserted_certainty} - before_certain
            if new_certain:
                add(
                    "claim_strength",
                    "Possible strengthening of a tentative claim: " + clause[:200],
                    before_clause,
                    clause,
                    "suspected",
                )
    checks = {
        "word_count_before": before_words,
        "word_count_after": after_words,
        "numbers_before": sorted(before_numbers),
        "numbers_after": sorted(after_numbers),
        "metric_values_before": sorted(before_metrics),
        "metric_values_after": sorted(after_metrics),
        "citations_before": sorted(before_cites),
        "citations_after": sorted(after_cites),
        "protected_terms": sorted(terms),
        "missing_terms": missing_terms,
        "unperformed_status_before": pending_before,
        "unperformed_status_after": pending_after,
        "scope": "Surface fidelity checks only; passing does not establish factual correctness or semantic equivalence.",
        "guard_version": "3.0-differential-local-scope",
        "identity_unchanged": identity_unchanged,
    }
    return {
        "passed": not issues,
        "issues": issues,
        "accepted": not issues,
        "reasons": issues,
        "checks": checks,
        "findings": findings,
        "hard_failure_count": sum((f["severity"] == "hard" for f in findings)),
        "suspected_failure_count": sum((f["severity"] == "suspected" for f in findings)),
        "requires_semantic_review": any((f["severity"] == "suspected" for f in findings)),
        "surface_decision": (
            "pass"
            if not findings
            else (
                "block_surface_mismatch"
                if any((f["severity"] == "hard" for f in findings))
                else "needs_semantic_review"
            )
        ),
    }
