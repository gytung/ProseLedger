# Evidence-Preserving Revision of Research Proposals

## Abstract

Research proposals must communicate clearly while distinguishing established findings from hypotheses and planned experiments. This project will investigate whether a claim-and-evidence ledger can guide language-model revision without weakening those distinctions. The proposed system will link factual claims to supplied evidence, record their qualifications, and check changes after revision. Evaluation will examine evidence preservation alongside readability and instruction following. The central question is whether explicit claim tracking improves factual fidelity while permitting useful editorial changes.

## Introduction

Revising a proposal involves more than correcting grammar: authors may reorganize arguments, compress background material, and clarify methods. These changes can inadvertently strengthen a qualified finding, detach a citation from its claim, or describe a planned experiment as completed. A fluent revision can therefore misrepresent the underlying research even when its sentences appear plausible.

This project will treat evidence preservation as an explicit revision objective. It will ask whether recording claim support and research status before editing helps maintain them afterward. The intended contribution is a revision procedure and evaluation protocol, rather than a guarantee that automated checks can establish scientific truth.

## Related Work

ALCE evaluates generated answers through fluency, correctness, and citation quality, and its authors report substantial remaining gaps in citation support [S1]. Attribute First, then Generate selects source segments before sentence planning and generation; its authors report more concise attributions and reduced human verification time in summarization and long-form question answering [S2]. These findings motivate explicit evidence links, but do not establish their effectiveness for proposal revision.

TETRA provides professionally edited academic documents and addresses the difficulty of evaluating revisions with many acceptable realizations [S3]. Research on scientific revision metrics reports that LLM judges assess instruction following more effectively than correctness, motivating complementary evaluation measures [S4]. RefChecker represents claims as triplets and checks them against references [S5]. The proposed ledger will adapt fine-grained checking to revision while explicitly retaining qualifications and planned-research status.

## Methodology

Each input will contain an original proposal, a revision instruction, and a bounded evidence packet. The system will first construct a ledger of substantive claims. Each entry will record the original wording, its role as a source finding, proposed method, hypothesis, or planned evaluation, and any relevant supporting passage. Qualifications such as uncertainty, population, and task scope will be recorded where applicable. Unsupported background assertions will be flagged for review.

A revision model will then receive the draft, instruction, and ledger. It will be allowed to restructure and rewrite the proposal while preserving supported meanings and research status. Afterward, a checker will align revised claims with ledger entries and inspect additions, omissions, and changes in scope or certainty. New proposed ideas will be distinguished from new factual assertions requiring support. Flagged changes will prompt a targeted correction or an author-facing explanation when the evidence cannot resolve them.

## Planned Evaluation

The study will assemble proposal–evidence pairs with annotations of claim support, qualifications, and research status. Comparisons will include ordinary instruction-based revision, revision with evidence access, and the complete ledger procedure, using matched model settings and editing instructions.

Blinded human assessors will judge clarity, coherence, instruction following, and fidelity to supplied evidence. Claim-level measures will track unsupported assertions, citation mismatches, lost qualifications, and changes from planned to completed research. Results will be reported separately to expose tradeoffs. Ablations will remove the ledger or post-revision checking to examine each component’s contribution. Evaluator disagreements will be documented and adjudicated.

## Limitations and Conclusion

Claim extraction and alignment may miss implicit meanings, while incomplete evidence limits support judgments. Ledger constraints may also discourage beneficial restructuring. The planned study will examine these failure modes alongside potential benefits. Its aim is to determine when explicit evidence tracking helps authors revise proposals clearly while preserving what is known, proposed, and still untested.