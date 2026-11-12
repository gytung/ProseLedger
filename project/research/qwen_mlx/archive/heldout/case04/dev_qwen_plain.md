# Preserving Negative Findings and Uncertainty in Literature Synthesis

## Abstract

Literature synthesis should communicate the support found in studies, what they fail to establish, and where uncertainty remains. This proposal explores whether an explicit evidence ledger can help language models preserve these distinctions. The proposed method will capture findings alongside their polarity, qualifications, and study conditions before generating a synthesis. Planned evaluation will assess evidence retention, attribution accuracy, readability, and verification effort without presuming that the method outperforms simpler approaches.

## Introduction

A synthesis can contain supported statements while omitting negative findings or qualifications that materially affect its interpretation. For example, a reported failure to detect an effect should not become evidence that no effect exists. Likewise, a result limited to particular conditions should not become an unrestricted conclusion. These distinctions motivate a research question: can structured evidence planning preserve consequential negative and uncertain findings without overwhelming readers?

The project will investigate fidelity to the supplied evidence, rather than infer the true state of an entire research field. Its intended contribution is a generation and evaluation procedure that makes omissions and changes in evidential strength inspectable.

## Related Work

Gao and colleagues introduce ALCE to evaluate citation-bearing generation through fluency, correctness, and citation quality, reporting substantial remaining gaps in citation support [S1]. This establishes a relevant evaluation foundation, although the supplied excerpts do not establish a dedicated measure of negative-finding retention.

Slobodkin and colleagues organize grounded generation into content selection, sentence planning, and sequential generation, using selected source segments as fine-grained attributions [S2]. The proposed method will adapt this planning structure by explicitly representing qualifications and findings that warrant inclusion. RefChecker extracts claim-triplets and checks them against references [S5]; this motivates granular verification, while our proposed representation will additionally retain uncertainty and scope. Jourdan and colleagues report that LLM judges struggle with correctness in scientific revision evaluation [S4], supporting the inclusion of human evidence checks.

## Methodology

Each source passage will be mapped into an evidence ledger containing the reported finding, its supporting span, the finding's polarity, expressions of uncertainty, relevant conditions, and stated limitations. The ledger will distinguish between an explicit negative finding, an inconclusive result, and information that is simply not present in the passage. In ambiguous cases, the source wording will be retained to avoid unjustified certainty.

A planning stage will identify evidence necessary to address the synthesis question, including qualifications that could alter a reader’s interpretation. Inclusion decisions will be based on relevance and impact, without a fixed quota for negative statements. The generator will then draft sentences linked to selected ledger entries, ensuring that differences between individual studies are preserved when aggregation would obscure disagreement.

Verification will operate in both directions. Output claims will be checked against their source spans for support, polarity, scope, and certainty. Selected ledger entries will also be reviewed against the draft to highlight any consequential omissions. Flagged passages will be revised and rechecked.

## Planned Evaluation

The study will assemble source bundles containing explicit negative, inconclusive, qualified, and conflicting findings. Independent annotators will identify relevant evidence units and adjudicate disagreements. Comparisons will include direct citation-based synthesis, attribution-first generation, and the proposed ledger method under matched source access and length budgets.

Human reviewers will assess supported-claim precision, retention of relevant negative and uncertain findings, changes in certainty, citation accuracy, and readability. Verification time will provide a complementary usability measure. Ablations will remove uncertainty fields or omission checking to examine their contributions. Results will include uncertainty estimates and qualitative error analysis; relevance judgments will be fixed before reviewers inspect system outputs.

## Limitations and Conclusion

A ledger cannot recover findings missing from the available sources or correct for publication bias. Annotation might also simplify nuanced scientific language, and preservation requirements could reduce concision. The study will thus test whether explicit evidence tracking enhances faithful synthesis under specific conditions, while documenting cases where its additional structure offers little benefit.