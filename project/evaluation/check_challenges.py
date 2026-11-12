import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'engine'))
import core

EDITS = [
    ('C01', 'The proposed experiment will therefore not estimate annual retreat rates', 'The proposed experiment will therefore estimate annual retreat rates', 'Negation removal changes a declared exclusion into a planned estimate.'),
    ('C02', 'arrivals from 18 weekdays', 'arrivals from 81 weekdays', 'The planned number of days changes from 18 to 81.'),
    ('C03', 'assign 30 seedlings to each condition and observe them for 12 days', 'assign 12 seedlings to each condition and observe them for 30 days', 'Sample size and duration are exchanged while the set of numeric tokens is unchanged.'),
    ('C04', 'a developer will retain authority over acceptance', 'the assistant will retain authority over acceptance', 'The actor holding the final decision changes from developer to assistant.'),
    ('C05', 'A blank maker field also does not establish that an object was made anonymously', 'A blank maker field also establishes that an object was made anonymously', 'Missing metadata is turned into evidence of anonymous production.'),
    ('C06', 'Equality is therefore not an exceedance', 'Equality is therefore an exceedance', 'The boundary convention changes from a strict threshold to an inclusive one.'),
    ('C07', 'no archival source has resolved the competing closure dates', 'an archival source has resolved the competing closure dates', 'An unresolved conflict is falsely described as resolved by archival evidence.'),
    ('C08', 'with the final 14 days held out from fitting', 'with the first 14 days held out from fitting', 'The temporal test split changes while its size is unchanged.'),
    ('C09', 'recovery relative to target material in the input, while purity uses recovered output mass', 'purity relative to target material in the input, while recovery uses recovered output mass', 'The definitions of recovery and purity exchange denominators.'),
    ('C10', 'only if both meet the recorded requirements', 'if either meets the recorded requirements', 'The verification conjunction changes to a disjunction.'),
    ('C11', 'It also does not assign course grades', 'It also assigns course grades', 'An explicitly excluded grading use becomes a claimed study function.'),
    ('C12', '1180 to 1260 CE', '1180 to 1261 CE', 'The upper endpoint of the date interval changes.')
]

BENIGN = [
    ('C01', 'A glacier outline can change because the ice moved or because the observation is incomplete.', 'A glacier outline may change because the ice moved or the observation is incomplete.'),
    ('C02', 'arrivals from 18 weekdays', 'arrivals from eighteen weekdays'),
    ('C03', 'The study is small and focuses on a short observation period.', 'The study is small and covers a short observation period.'),
    ('C04', 'General advice can be correct in principle yet difficult to apply to a particular function.', 'General advice may be correct in principle but difficult to apply to a particular function.'),
    ('C05', 'The source records may themselves be incomplete or inconsistent.', 'The source records themselves may be incomplete or inconsistent.'),
    ('C06', 'The raw readings will remain available for inspection.', 'The raw readings will remain available to inspect.'),
    ('C07', 'The study cannot resolve the underlying historical disagreement.', 'The study cannot resolve the historical disagreement itself.'),
    ('C08', 'A short series from one building cannot establish performance across seasons or sites.', 'A short series from one building cannot establish performance across different seasons or sites.'),
    ('C09', 'The comparison is limited to the supplied material stream and sorting conditions.', 'The comparison concerns only the supplied material stream and sorting conditions.'),
    ('C10', 'The records may become outdated, and accessibility needs differ between users.', 'The records may become outdated, and users differ in their accessibility needs.'),
    ('C11', 'A single review cannot show whether a student later learns the underlying concept.', 'A single review cannot establish whether a student later learns the underlying concept.'),
    ('C12', 'The proposed study concerns the communication of existing evidence, not a new dating analysis.', 'The proposed study concerns how existing evidence is communicated, not a new dating analysis.')
]


def main():
    results = []
    for truth, cases in ((False, EDITS), (True, BENIGN)):
        for record in cases:
            case_id, before, after = record[:3]
            item = json.loads((ROOT / 'inputs' / (case_id + '.json')).read_text())
            text = item['draft']
            if before not in text:
                raise ValueError('Challenge anchor missing: ' + case_id)
            candidate = text.replace(before, after, 1)
            check = core.guard(text, candidate, item['sources'])
            results.append({'caseId': case_id, 'challenge': 'benign' if truth else 'violation',
                            'expectedPass': truth, 'actualPass': check['passed'],
                            'correct': truth == check['passed'], 'findings': check['findings'],
                            'before': before, 'after': after,
                            'referenceReason': record[3] if len(record) > 3 else 'Meaning-preserving paraphrase; numerical wording may change form without changing value.'})
    outcome = {'scope': 'Deterministic guard only; constructed known-answer mutations, not full-pipeline or human evaluation.',
               'cases': results, 'correct': sum(x['correct'] for x in results), 'total': len(results),
               'truePositive': sum(not x['expectedPass'] and not x['actualPass'] for x in results),
               'falseNegative': sum(not x['expectedPass'] and x['actualPass'] for x in results),
               'trueNegative': sum(x['expectedPass'] and x['actualPass'] for x in results),
               'falsePositive': sum(x['expectedPass'] and not x['actualPass'] for x in results)}
    (ROOT / 'known_answer_challenges.json').write_text(json.dumps(outcome, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in outcome.items() if k != 'cases'}))


if __name__ == '__main__':
    main()
