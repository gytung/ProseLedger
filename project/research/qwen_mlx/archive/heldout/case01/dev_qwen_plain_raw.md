# Evidence-Linked Revision of Scientific Proposals

## Abstract

Scientific proposal revision must improve expression while maintaining the distinction between established findings and proposed research. This project investigates an evidence-linked revision workflow that links factual claims to supplied source excerpts and tracks their status throughout editing. The hypothesis is that explicit claim tracking can reduce unsupported changes while preserving useful improvements in clarity and coherence. The planned evaluation will compare this workflow with direct and citation-aware revisions, using expert assessments of writing quality, evidential support, and research intent preservation.

## Introduction

A proposal synthesizes literature findings, interpretations, hypotheses, and planned experiments. Revisions can blur these categorizations: a qualified finding may strengthen to a firm assertion, and a planned evaluation might acquire language suggesting it has been completed. Fluent prose alone cannot ensure such changes remain valid.

The proposed workflow aims to make these distinctions clear during revision. Its primary research question is whether linking claims and edits to specific evidence helps preserve their support while permitting legitimate restructuring. The project will evaluate both the factual reliability and practical usefulness of the resulting prose, acknowledging that additional constraints may sometimes impede revision.

## Related Work

ALCE evaluates generated answers for fluency, correctness, and citation quality, highlighting the ongoing challenge of robust citation support in evaluated settings [S1]. Attribute First, then Generate pre-selects source segments before generating sentences, leading to more concise attributions and reduced human verification time in summarization and long-form question answering [S2]. These results underscore the importance of explicit evidence selection, though they do not demonstrate its effectiveness for proposal revision.

TETRA supplies professionally revised academic texts and analyzes document-level changes such as coherence and consistency [S3]. Research indicates that LLM judges perform better on instruction-following than on assessing correctness, underscoring the value of complementary evaluation methods [S4]. RefChecker identifies claim-triplets and verifies them against references [S5]. This proposal aims to adapt evidence linking and claim checking for revisions that must also maintain future research commitments.

## Methodology

Inputs will include a proposal draft, a revision instruction, and a collection of source excerpts. The system will identify claims and classify them as source findings, author interpretations, hypotheses, or planned procedures. Source findings will be linked to supporting excerpt spans, while other categories will retain explicit status labels without being treated as established evidence.

Before rewriting, the system will prepare an edit plan that connects substantive changes to affected claims. It will then generate revised prose and compare the original and revised claim records. Checks will target altered scope, lost qualifications, unsupported additions, and changes from planned to completed work. When necessary, the workflow will flag issues for author review. A compact change record will expose evidence links and unresolved questions.

## Planned Evaluation

A study will use proposal drafts paired with revision instructions and excerpt collections. Conditions will include direct instruction-based revision, revision with document-level citations, and the proposed workflow, holding the underlying model and evidence constant. Blinded expert reviewers will assess clarity, coherence, instruction fulfillment, support preservation, and fidelity to the intended research. Separate annotations will identify unsupported factual additions and changes in experimental status. Verification time will measure review effort. Ablations will remove excerpt-level links or claim-status tracking to examine their respective contributions. Paired analyses will report uncertainty and tradeoffs, with automated checks supplementing expert judgments.

## Limitations and Conclusion

Supplied excerpts may lack qualifications, and claim classification may oversimplify nuanced arguments. Evidence links can verify only the claims within the provided sources. Expert review will remain essential. The project aims to develop a testable revision workflow and evaluation protocol to determine whether clearer proposals can maintain their evidential boundaries.