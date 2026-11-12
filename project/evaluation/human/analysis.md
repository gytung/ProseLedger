# Human evaluation export analysis

## Verified aggregate results

Source identification: 10 item responses; 4 correct, 5 incorrect, 1 cannot tell. Correct/all = 40%; correct/decisive = 44.44%. Published-source sides are balanced, five A and five B. Five generated passages were chosen as the published source. This is five decisions, not five distinct people.

Fluency: 10 item responses; the finalized UI reports retained revision preferred in 4, original preferred in 5 and cannot tell in 1. Revised/all = 40%; revised/decisive = 44.44%. The raw export allows A/B counts but omits the branch key and compared passages. The aggregate treatment mapping is verified against the UI, not independently recalculated from individual text pairs.

Both exports contain a single response-record group. The organizer estimates approximately ten classmates, with one person reportedly completing both tasks and approximately two items per person under shared codes. This is recruitment recollection, not a verified count of independent raters; item-to-person assignment is unavailable. All 100 possible feature-scale entries in the source study are null.

## Item-level audit

| Source item | Published side | Selected side | Result | Generated words | Published words | Fluency item | Selected side |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| S3-01 | A | A | correct | 54 | 44 | FL-01 | B |
| S3-02 | B | B | correct | 65 | 55 | FL-02 | B |
| S3-03 | A | B | incorrect | 70 | 68 | FL-03 | B |
| S3-04 | B | B | correct | 77 | 74 | FL-04 | Cannot tell |
| S3-05 | A | A | correct | 96 | 99 | FL-05 | A |
| S3-06 | B | A | incorrect | 75 | 62 | FL-06 | B |
| S3-07 | A | B | incorrect | 62 | 65 | FL-07 | B |
| S3-08 | B | Cannot tell | cannot_tell | 58 | 64 | FL-08 | A |
| S3-09 | A | B | incorrect | 42 | 40 | FL-09 | A |
| S3-10 | B | A | incorrect | 66 | 63 | FL-10 | A |

## Text provenance and lengths

Generated passages average 66.5 words (range 42–96); published passages average 63.4 words (range 40–99). They are short excerpts, not complete manuscripts. These length statistics do not remove topic, publication-era or genre confounding.

After word/punctuation normalisation, S3-03, S3-04, S3-05 and S3-10 match passages in dev_initial.md, the seen development document from the Qwen study. Several also recur unchanged in fallback or other development outputs, so the matching text cannot determine which treatment generated the survey material. Other generated items have no complete normalised match in the inspected study Markdown archive. The fluency export lacks text, so its overlap with the detector cohort cannot be verified.

## Interpretation

The source task is a paired choice of the published excerpt, not a balanced binary text classification task. Publication is an operational provenance label and does not prove unaided human authorship. The fluency result does not establish an overall preference for revisions. These observations support a descriptive pilot and motivate fuller blinded evaluation with anonymous participant identifiers, item-to-run mappings and preserved original/revised assignments.