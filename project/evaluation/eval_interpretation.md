# Interpretation of the controlled revision study

## What the comparison establishes

The study asks whether explicit naturalization instructions add value under a fixed writer and verifier. Twelve controlled proposals were frozen before inference, each with six sections, two source packets and six reference requirements. Generic and Rules received the same original, evidence, Qwen2.5-7B-Instruct Q4_K_M writer, section seeds and six writing opportunities. Both used the same section review, bounded repair and final admission procedure. Generic retained the shared preservation requirements. The comparison measures an editing instruction package against a verified baseline.

Rules combines six principles with an academic copy-editing instruction: identify the actor and action, use supported concrete wording, remove redundancy without removing qualifications, preserve logical relations, improve sentence focus and calibrate claims. This tests the package, not each principle separately. The manuscripts cover different topics and evidential difficulties; they are constructed inputs rather than randomly sampled submissions.

## Naturalness and order sensitivity

The branch-blinded evaluator consistently preferred Rules in seven cases and Generic in two; three cases were inconclusive across the two display orders. All three remain in the reported outcome. In C01, the preference reversed; C07 changed between a tie and Rules, and C09 between Generic and a tie. A single ordering would therefore give a less dependable comparison.

The evaluator assessed idiomatic phrasing, flow, direct wording and qualification, not authorship. Separate calls used the same hosted model as the reviewer: this is an automated preference measure, not an independent human assessment. In C04, Generic retained the original manuscript and was preferred to Rules. More editing is consequently not evidence of better writing.

## Preservation of the reference requirements

Both conditions received consistent “preserved” judgments for all 72 reference requirements across the two orders. The denominator is 72 requirements per condition, not 144 independent facts. Some requirements combine related commitments. The result concerns these specified requirements in retained outputs, not every possible proposition or unsupported addition.

For 71 requirements per condition, both supporting quotations were exact contiguous substrings. The remaining C04 requirement, “36 small Python functions”, combines evidence from two individually matching passages. Its failed contiguous-quote check is a formatting issue, not an observed content loss. Both passages and the original judgments remain inspectable.

## What verification contributes

The execution traces expose failures that a final-output comparison alone would conceal. Section reviewers reported 17 findings across 13 Generic sections and 14 findings across 11 Rules sections. Bounded repairs were accepted for 13 and 10 sections, respectively. One Rules patch set attempted a valid deletion but failed the nonempty-replacement constraint; that section reverted to its original. Generic retained a new candidate in 11 of 12 cases, whereas Rules did so in all 12. The final outputs contained 66 and 69 changed sections, respectively, out of 72 opportunities.

The known-answer checker experiment explains the division of labour between lexical and semantic checks. On 12 invalid edits and 12 valid paraphrases, the deterministic guard made 13 correct decisions. The semantic auditor made 24, and their conjunction made 23. Semantic review detected changes to negation, roles, temporal scope and metric definitions that preserved the visible vocabulary or number set. The conjunction still rejected the valid conversion of “18” to “eighteen”. These counts characterize coverage on the fixed mutation suite, rather than accuracy on an unspecified population of manuscripts.

Conservatism also has a cost. C04 Generic was rejected because the auditor distinguished an explicit reporting commitment from a close statement of the limitation of testing. That is a useful case for human equivalence annotation before changing the threshold for rejection. The appropriate response is to calibrate such decisions, not to remove fidelity checks whenever they prevent a stylistic change.

## Computational work and the response to feedback

All 24 writing runs completed. Each condition used 72 local writer responses and 30 hosted review or repair responses. Mean active model time was 138.19 seconds for Generic and 138.17 seconds for Rules. Mean per-run wall time, including waiting for the serialized local writer, was 204.28 and 187.77 seconds. The generation cohort spanned 2,407.23 seconds on the measured Mac. These timings do not establish a speed advantage: the scheduler overlapped hosted review with local writing. Token use and the additional 48 evaluation calls are reported separately; matched writer opportunities do not imply identical total token budgets.

GPTZero returned AI-class probability 1.0 for every original and retained text: 36 case-condition mappings from 35 unique scans. Neither condition reduced this endpoint on any of the 12 cases. The recorded detector version was `2026-11-04-base`; these observations remain separate from the earlier MLX pilot and its detector version. The positive automated prose preferences therefore do not establish a detector-score reduction.

The study turns “make the language more natural” into an inspectable procedure and comparison. It supports further investigation of explicit editing rules and identifies concrete priorities: equivalent-number normalization, bounded deletions and calibrated near-paraphrase rejection. These results concern writing instructions and revision governance, not a demonstrated benefit from historical experience-card retrieval.
