import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHOICES = [
    ('C01', 'rules', 'unsupported causal connection', 'Unsupported causal link',
     'A connective added for fluency can introduce a causal claim absent from the source.',
     'Require each added causal relation to be supported by a source span; otherwise preserve the two statements without a causal connector.'),
    ('C01', 'rules', 'definite prediction', 'Modality strengthened',
     'A possible trade-off becomes a promised consequence.',
     'Compare the scope of modal verbs in addition to surface grammar, and reject unsupported increases in certainty.'),
    ('C01', 'rules', 'patch_type', 'Valid deletion rejected by the repair schema',
     'The model proposed removing an unsupported clause, but an empty replacement fails the current nonempty-after constraint.',
     'Permit deletion patches when a unique exact anchor, coverage bound and post-edit semantic audit all pass; test this change on separate data.'),
    ('C02', 'generic', 'ensure accurate reliability', 'Bias mitigation presented as a guarantee',
     'Retaining difficult days reduces one selection risk but cannot guarantee accurate reliability estimates.',
     'Preserve the qualified relationship between the procedure and the risk it addresses.'),
    ('C02', 'rules', 'awkward comparative', 'Grammar worsens during naturalization',
     'The revision combines two incompatible comparative constructions.',
     'Check local grammar independently of lexical simplification; keep the original construction when the change is not an improvement.'),
    ('C02', 'rules', 'favourable definition', 'Concrete evaluation safeguard omitted',
     'A general promise of neutrality replaces the explicit restriction against selecting a favourable threshold definition.',
     'Represent fixed methodological safeguards as content commitments, not removable stylistic detail.'),
    ('C03', 'rules', 'Until', 'Temporal scope altered',
     'A rule fixed before observation is rewritten as a rule maintained only until observation starts.',
     'Check temporal connectors as relations, because the same nouns and numbers do not guarantee the same commitment.'),
    ('C04', 'generic', 'omits the explicit commitment', 'Conservative whole-document rejection',
     'The auditor distinguishes a reporting commitment from a close statement about test limitations; the entire candidate is consequently rejected.',
     'Obtain human equivalence labels for borderline cases and calibrate the rejection policy; this observation is a possible over-rejection, not a confirmed false positive.'),
    ('C05', 'rules', 'role of an editor', 'Assessor role changed',
     'An editorial simplification shifts the stated assessor from an editor to the study authors.',
     'Preserve who performs each action, especially when review responsibilities are part of the design.'),
    ('C06', 'generic', 'blanket causal guarantee', 'Controlled comparison overinterpreted',
     'Holding one factor fixed is rewritten as establishing the sole cause of any observed difference.',
     'Separate the factor controlled by the design from the causal conclusion that the evidence would support.'),
    ('C06', 'generic', 'added citation attributes', 'Citation scope expanded',
     'A citation is attached to additional limitations that are not stated in that source packet.',
     'Check the proposition supported by each citation occurrence rather than only whether the identifier is allowed.'),
    ('C08', 'rules', 'removes the citation', 'Citation occurrence lost',
     'A requirement remains in prose but loses its explicit source attribution.',
     'Retain section-level citation occurrence checks and expose the rejection reason in the ledger.'),
    ('C09', 'generic', 'implied subject', 'Dangling modifier introduced',
     'The rewritten clause grammatically assigns calculation to the recovered material rather than to the researchers.',
     'Check the actor of a shortened clause; a concise sentence is not automatically a coherent sentence.')
]


def main():
    events = json.loads((ROOT / 'observed_failure_events.json').read_text())['events']
    selected = []
    for case, condition, match, title, cause, next_step in CHOICES:
        found = next((x for x in events if x['caseId'] == case and x['condition'] == condition and match.lower() in x.get('problem', x.get('reason', '')).lower()), None)
        if found:
            selected.append({'failureId': 'F' + str(len(selected)+1).zfill(2), 'title': title,
                             'analysis': cause, 'nextStep': next_step, 'observedEvent': found})
    component = json.loads((ROOT / 'known_answer_challenges.json').read_text())['cases']
    finding = next(x for x in component if x['caseId'] == 'C02' and x['challenge'] == 'benign')
    selected.append({'failureId': 'F' + str(len(selected)+1).zfill(2),
                     'title': 'Equivalent numeric wording rejected',
                     'analysis': 'Changing 18 to eighteen preserves the quantity but removes a digit token. The lexical gate rejects this valid paraphrase even though the semantic auditor accepts it.',
                     'nextStep': 'Normalize equivalent number expressions before comparing quantities and retain role-sensitive semantic checks for swapped values.',
                     'observedEvent': finding, 'source': 'known_answer_challenges.json; semantic_challenges/C02_benign/result.json'})
    output = {'scope': 'Evidence-backed case analyses. Candidate findings were usually repaired or rolled back; they are not presented as errors in every final output. Possible auditor over-rejection is distinguished from known-answer false positives.',
              'count': len(selected), 'cases': selected}
    (ROOT / 'curated_failure_cases.json').write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(json.dumps({'curatedCases': len(selected)}))


if __name__ == '__main__':
    main()
