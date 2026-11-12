# Preserving Citation Support During Cross-Section Editing

## Abstract

Academic revision often moves, merges, or rewrites claims across sections. A citation can survive these operations even when it no longer supports the revised statement. This project proposes a claim–evidence ledger that tracks relationships between manuscript claims and supporting source passages throughout editing. The research question is whether tracking these relationships can preserve citation support while allowing useful restructuring. Planned experiments will compare ledger-assisted editing with ordinary revision and citation-preservation prompts, assessing both attribution and writing quality.

## Introduction

Cross-section editing changes more than sentence location. Moving a qualified observation from a discussion into an introduction may broaden its apparent scope; merging sentences may attach one citation to several distinct claims. These examples motivate a distinction between retaining citation markers and retaining evidential support.

The proposed system will treat each citation as a relationship requiring reassessment when its associated claim changes. Its purpose is to help authors retain supported content and identify revisions requiring verification. The hypothesis is that explicit tracking can reduce unsupported attribution without preventing legitimate paraphrasing or reorganization. Whether this tradeoff is achievable will remain an empirical question.

## Related Work

Gao and colleagues introduce ALCE and evaluate generated answers along fluency, correctness, and citation quality dimensions [S1]. Their findings motivate evaluating support separately from readability. Slobodkin and colleagues select source segments before sentence planning and generation, reporting more concise attributions and reduced human verification time in their evaluated tasks [S2]. This proposal adapts the idea of explicit evidence selection to revision rather than initial generation.

TETRA provides professionally edited academic texts and addresses document-level coherence and consistency [S3]. Jourdan and colleagues report complementary strengths of task-specific metrics and LLM judges, including difficulties judging correctness [S4]. RefChecker represents claims as triplets checked against references [S5]. These supplied excerpts inform the design but do not establish performance on citation preservation during cross-section editing.

## Methodology

The system will first build a ledger connecting manuscript claims, citation identifiers, and supporting source passages. Each entry will retain relevant qualifications, such as population, conditions, and uncertainty. Authors will be able to correct the initial mapping before revision.

After an edit, an alignment component will identify retained, relocated, split, merged, and newly introduced claims. It will use both semantic correspondence and edit history where available. Candidate evidence links will follow aligned claims, but their support status will be reassessed against the revised wording and surrounding context.

For each relationship, the system will distinguish supported, contradicted, and unresolved cases. Unresolved cases will include insufficient evidence or ambiguous alignment. A proposed repair may restore a qualification, narrow a claim, or flag the passage for author review. The system will not assume that a nearby citation supports every clause or that deleting a difficult claim constitutes successful preservation.

## Planned Evaluation

An evaluation set will pair academic passages and their cited evidence with instructions to relocate arguments, consolidate repeated claims, or rewrite material across sections. Human annotators will assess initial support and revised claim–evidence relationships.

Comparisons will include ordinary editing, explicit citation-preservation prompting, and ledger-assisted editing under matched model and evidence conditions. Assessments will cover unsupported attribution, supported-claim retention, citation completeness, instruction fulfillment, and coherence. Blinded reviewers will inspect source passages; automated checks will supplement their judgments. Ablations will remove persistent claim identities or post-edit support checking. Analysis will examine whether apparent preservation gains arise from avoiding requested edits, deleting content, or producing less readable prose.

## Limitations and Conclusion

Claim alignment may fail when revisions substantially reorganize arguments. Source passages may also omit context needed to judge support, while automated checkers can misinterpret qualifications. Human review will therefore remain necessary for unresolved cases. The intended contribution is an editing method and evaluation protocol that test citation preservation as continued evidential support across revisions.