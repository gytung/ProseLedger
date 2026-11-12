# Preserving Negative Findings and Uncertainty in Literature Synthesis

## Abstract

Literature synthesis should communicate the support found in studies, what they fail to establish, and where uncertainty remains. This proposal explores whether an explicit evidence ledger can help language models preserve these distinctions. The proposed method will capture findings alongside their polarity, qualifications, and study conditions before generating a synthesis. Planned evaluation will assess evidence retention, attribution accuracy, readability, and verification effort without presuming that the method outperforms simpler approaches.

## Introduction

A synthesis can contain supported statements while omitting negative findings or qualifications that materially affect its interpretation. For example, a reported failure to detect an effect should not be treated as evidence that no effect exists. Similarly, a result limited to specific conditions should not be generalized beyond those conditions. These considerations motivate the research question: can structured evidence planning preserve consequential negative and uncertain findings without causing undue confusion for readers?

The project aims to ensure fidelity to the provided evidence rather than making inferences about the broader state of the research area. The intended contribution is a generation and evaluation framework that makes evidence omissions and shifts in strength transparent and verifiable.

## Related Work

Gao and colleagues introduce ALCE to evaluate citation-bearing generation through fluency, correctness, and citation quality, reporting significant gaps in citation support [S1]. This provides a relevant evaluation framework, though it does not specifically measure the retention of negative findings.

Slobodkin and colleagues organize grounded generation into content selection, sentence planning, and sequential generation, using selected source segments as fine-grained attributions [S2]. The proposed method will adapt this planning structure by explicitly representing qualifications and findings that require inclusion. RefChecker extracts claim-triplets and verifies them against references [S5], motivating granular verification, while our proposed representation will additionally retain uncertainty and scope. Jourdan and colleagues report that LLM judges struggle with correctness in scientific revision evaluation [S4], supporting the inclusion of human evidence checks.

## Methodology

Each source passage will be mapped into an evidence ledger containing the reported finding, its supporting span, the finding's polarity, expressions of uncertainty, relevant conditions, and stated limitations. The ledger will distinguish between an explicit negative finding, an inconclusive result, and information that is simply not present in the passage. In ambiguous cases, the source wording will be retained to avoid unjustified certainty.

A planning stage will identify evidence necessary to address the synthesis question, including qualifications that could alter a reader’s interpretation. Inclusion decisions will be based on relevance and impact, without a fixed quota for negative statements. The generator will then draft sentences linked to selected ledger entries, ensuring that differences between individual studies are preserved when aggregation would obscure disagreement.

Verification will operate in both directions. Output claims will be checked against their source spans for support, polarity, scope, and certainty. Selected ledger entries will also be reviewed against the draft to highlight any consequential omissions. Flagged passages will be revised and rechecked.

## Planned Evaluation

The study will assemble source bundles containing explicit negative, inconclusive, qualified, and conflicting findings. Independent annotators will identify relevant evidence units and resolve disagreements. Comparisons will include direct citation-based synthesis, attribution-first generation, and the proposed ledger method under matched source access and length constraints.

Human reviewers will evaluate supported-claim precision, retention of relevant negative and uncertain findings, changes in certainty, citation accuracy, and readability. Verification time will serve as a complementary measure of usability. Ablations will remove uncertainty fields or omission checking to assess their impact. Results will include uncertainty estimates and qualitative error analysis; relevance judgments will be finalized before reviewers assess system outputs.

## Limitations and Conclusion

A ledger cannot recover findings missing from the available sources or correct for publication bias. Annotation might also simplify nuanced scientific language, and preservation requirements could reduce concision. The study will thus test whether explicit evidence tracking enhances faithful synthesis under specific conditions, while documenting cases where its additional structure offers little benefit.