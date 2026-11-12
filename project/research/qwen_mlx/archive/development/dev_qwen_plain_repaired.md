# Evidence-Preserving Revision of Research Proposals

## Abstract

Research proposals must communicate clearly and distinguish between established findings and hypotheses or planned experiments. This project will explore whether a claim-and-evidence ledger can guide language-model revision while maintaining these distinctions. The proposed system will link factual claims to supplied evidence, record their qualifications, and check changes after revision. Evaluation will assess evidence preservation alongside readability and adherence to instructions. The central question is whether explicit claim tracking enhances factual fidelity while allowing for useful editorial modifications.

## Introduction

Revising a proposal involves more than correcting grammar; authors may reorganize arguments, compress background material, and clarify methods. These changes can inadvertently strengthen a qualified finding, detach a citation from its claim, or describe a planned experiment as completed. A fluent revision can thus misrepresent the underlying research, even when its sentences appear plausible.

This project aims to treat evidence preservation as an explicit revision objective, asking whether recording claim support and research status before editing helps maintain them afterward. The intended contribution is a revision procedure and evaluation protocol, rather than a guarantee that automated checks can establish scientific truth.

## Related Work

ALCE evaluates generated answers for fluency, correctness, and citation quality, but its authors note significant gaps in ensuring proper citation support [S1]. Attribute First, then Generate involves selecting source segments before sentence planning and generation; its authors report more concise attributions and reduced human verification time in summarization and long-form question answering [S2]. These findings suggest the need for explicit evidence links, but these findings do not establish their effectiveness for research proposal revision.

TETRA offers professionally edited academic documents and tackles the challenge of evaluating revisions with multiple acceptable outcomes [S3]. Research on scientific revision metrics indicates that language models are better at assessing whether instructions are followed than at evaluating correctness, prompting the use of additional evaluation methods [S4]. RefChecker models claims as triplets and verifies them against references [S5]. The proposed ledger will adapt fine-grained checking for revision while explicitly retaining qualifications and planned-research status.

## Methodology

Each input will include an original proposal, a revision instruction, and a bounded evidence packet. First, the system will create a ledger of substantive claims, recording the original wording, the claim's role as a source finding, proposed method, hypothesis, or planned evaluation, and any relevant supporting passage. Qualifications like uncertainty, population, and task scope will be noted as needed. Unsupported background assertions will be flagged for review.

Next, a revision model will receive the draft, instruction, and ledger. The model will be permitted to restructure and rewrite the proposal while maintaining supported meanings and research status. Following the revision, a checker will align the revised claims with ledger entries and inspect additions, omissions, and changes in scope or certainty. New proposed ideas will be distinguished from new factual assertions needing support. Flagged changes will prompt a targeted correction or an author-facing explanation when the evidence cannot resolve them.

## Planned Evaluation

The study will assemble proposal–evidence pairs with annotations of claim support, qualifications, and research status. Comparisons will include ordinary instruction-based revision, revision with evidence access, and the complete ledger procedure, using matched model settings and editing instructions.

Blinded human assessors will evaluate clarity, coherence, instruction following, and fidelity to supplied evidence. Claim-level measures will track unsupported assertions, citation mismatches, lost qualifications, and changes from planned to completed research. Results will be reported separately to highlight tradeoffs. Ablations will remove the ledger or post-revision checking to examine each component’s contribution. Evaluator disagreements will be documented and adjudicated.

## Limitations and Conclusion

Claim extraction and alignment may miss implicit meanings, while incomplete evidence restricts support judgments. Ledger constraints could also impede beneficial restructuring. The planned study will investigate these challenges alongside potential benefits, aiming to discern when explicit evidence tracking aids authors in revising proposals clearly while preserving what is known, proposed, and still untested.