import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    source = json.loads((ROOT / 'source_public.json').read_text(encoding='utf-8'))
    fluency = json.loads((ROOT / 'fluency_public.json').read_text(encoding='utf-8'))
    outcomes = Counter()
    for item in source['items']:
        answer = item['chosen_published_material']
        outcome = 'cannot_tell' if answer == 'Cannot tell' else (
            'correct' if answer == item['published_material'] else 'incorrect')
        outcomes[outcome] += 1
    for field in ('correct', 'incorrect', 'cannot_tell'):
        if outcomes[field] != source['summary'][field]:
            raise ValueError('Source summary differs from item records.')
    responses = Counter(item['chosen_more_natural'] for item in fluency['responses'])
    for answer, field in [('A', 'a_choices'), ('B', 'b_choices'), ('Cannot tell', 'cannot_tell')]:
        if responses[answer] != fluency['summary'][field]:
            raise ValueError('Fluency choice summary differs from item records.')
    print(json.dumps({
        'sourceItemOutcomes': dict(outcomes),
        'fluencyPositionChoices': dict(responses),
        'fluencyRevisedPreferred': fluency['summary']['revised_preferred'],
        'fluencyAggregateProvenance': fluency['branch_mapping_evidence'],
        'distinctRaterCount': None,
        'scope': 'Counts of submitted comparisons. Revised-versus-original fluency '
                 'aggregate comes from the recorded application result page; '
                 'the exported per-item side key is unavailable.'
    }, indent=2))


if __name__ == '__main__':
    main()
