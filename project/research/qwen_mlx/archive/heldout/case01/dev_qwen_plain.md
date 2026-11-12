# Evidence-Linked Revision of Scientific Proposals

## Abstract

Scientific proposal revision must improve expression while preserving the distinction between established findings and proposed research. This project will investigate an evidence-linked revision workflow that associates factual claims with supplied source excerpts and tracks their status through editing. The central hypothesis is that explicit claim tracking can reduce unsupported changes while retaining useful improvements in clarity and coherence. Planned evaluation will compare this workflow with direct revision and citation-aware revision using expert assessments of writing quality, evidential support, and preservation of research intent.

## Introduction

A proposal synthesizes literature findings, interpretations, hypotheses, and planned experiments. Revisions can blur these categorizations: a qualified finding may strengthen to a firm assertion, and a planned evaluation might acquire language suggesting it has been completed. Fluent prose alone cannot ensure such changes remain valid.

The proposed workflow aims to make these distinctions clear during revision. Its primary research question is whether linking claims and edits to specific evidence helps preserve their support while permitting legitimate restructuring. The project will evaluate both the factual reliability and practical usefulness of the resulting prose, acknowledging that additional constraints may sometimes impede revision.

## Related Work

ALCE evaluates generated answers along fluency, correctness, and citation quality, demonstrating that citation support remains challenging in the authors’ evaluated settings [S1]. Attribute First, then Generate selects source segments before sentence generation; its authors report more concise attributions and reduced human verification time in summarization and long-form question answering [S2]. These findings motivate explicit evidence selection, but do not establish effectiveness for proposal revision.

TETRA provides professionally revised academic texts and examines document-level changes such as coherence and consistency [S3]. Research on scientific revision evaluation reports that LLM judges handle instruction-following better than correctness, supporting the use of complementary evaluation methods [S4]. RefChecker extracts claim-triplets and checks them against references [S5]. This proposal will explore how evidence linking and claim checking can be adapted to revisions that must also preserve future research commitments.

## Methodology

Inputs will comprise a proposal draft, a revision instruction, and a bounded collection of source excerpts. The system will identify claims and classify their roles as source findings, author interpretations, hypotheses, or planned procedures. Source findings will receive links to supporting excerpt spans; other categories will retain explicit status labels without being treated as established evidence.

Before rewriting, the system will prepare an edit plan connecting substantive changes to affected claims. It will then generate revised prose and compare the original and revised claim records. Checks will target altered scope, lost qualifications, unsupported additions, and changes from planned to completed work. When supplied evidence is insufficient, the workflow will flag the issue for author review. A compact change record will expose evidence links and unresolved questions.

## Planned Evaluation

A study will use proposal drafts paired with revision instructions and excerpt collections. Conditions will include direct instruction-based revision, revision with document-level citations, and the proposed workflow, holding the underlying model and evidence constant. Blinded expert reviewers will assess clarity, coherence, instruction fulfillment, support preservation, and fidelity to the intended research. Separate annotations will identify unsupported factual additions and changes in experimental status. Verification time will measure review effort. Ablations will remove excerpt-level links or claim-status tracking to examine their respective contributions. Paired analyses will report uncertainty and tradeoffs, with automated checks supplementing expert judgments.

## Limitations and Conclusion

Supplied excerpts may omit qualifications, and claim classification may misrepresent nuanced arguments. Evidence links cannot establish truth beyond the available material. Expert review will therefore remain necessary. The intended contribution is a testable revision workflow and evaluation protocol for examining whether clearer proposals can also preserve their evidential boundaries.