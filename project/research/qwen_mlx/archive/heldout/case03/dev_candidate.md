# Preserving Citation Support During Cross-Section Editing

## Abstract

Academic revision frequently relocates, merges, or rewrites claims across sections. While a citation may persist through these changes, it may no longer support the revised statement. This project proposes a claim–evidence ledger to track relationships between manuscript claims and their supporting source passages throughout editing. The core research question is whether such tracking can preserve citation support while facilitating useful restructuring. The planned experiments will compare ledger-assisted editing to ordinary revision and explicit citation-preservation prompts, evaluating both attribution and writing quality.

## Introduction

Cross-section editing alters more than just sentence location. Moving a qualified observation from a discussion into an introduction can broaden its apparent scope; merging sentences may link a single citation to multiple distinct claims. These examples highlight the distinction between retaining citation markers and ensuring that the cited evidence still supports the claims.

The proposed system views each citation as a relationship needing reassessment when its associated claim changes. Its aim is to help authors retain evidence-supported content and identify revisions that require verification. The hypothesis is that explicit tracking can mitigate unsupported attribution while still supporting legitimate paraphrasing and reorganization. Whether this balance is achievable remains an empirical question.

## Related Work

Gao and colleagues introduce ALCE, evaluating generated answers based on fluency, correctness, and citation quality [S1]. Their work suggests evaluating support independently of readability. Slobodkin and colleagues select source segments before sentence planning and generation, resulting in more concise attributions and reduced human verification time in their tasks [S2]. This proposal adapts the concept of explicit evidence selection for use in cross-section editing, rather than initial generation.

TETRA offers professionally edited academic texts with a focus on document-level coherence and consistency [S3]. Jourdan and colleagues highlight the complementary strengths of task-specific metrics and LLM judges, noting the challenges in judging correctness [S4]. RefChecker represents claims as triplets checked against references [S5]. These supplied excerpts inform our design but do not establish performance on citation preservation during cross-section editing.

## Methodology

The system will first create a ledger connecting manuscript claims, citation identifiers, and supporting source passages. Each entry will include relevant qualifications, such as population, conditions, and uncertainty. Authors will be able to correct the initial mapping before any revisions.

After an edit, an alignment component will identify retained, relocated, split, merged, or newly introduced claims. It will use both semantic correspondence and edit history when available. Candidate evidence links will follow aligned claims and will be reassessed against the revised wording and context.

For each relationship, the system will categorize it as supported, contradicted, or unresolved. Unresolved cases will include insufficient evidence or ambiguous alignment. A proposed repair may restore qualifications, narrow claims, or flag passages for author review. The system will not assume that a nearby citation supports every clause or that deleting a difficult claim constitutes successful preservation.

## Planned Evaluation

An evaluation set will pair academic passages with their cited evidence and instructions to relocate arguments, consolidate repeated claims, or rewrite material across sections. Human annotators will assess initial support and the revised claim–evidence relationships.

Comparisons will include ordinary editing, explicit citation-preservation prompting, and ledger-assisted editing under matched model and evidence conditions. Assessments will cover unsupported attribution, retained supported claims, citation completeness, adherence to instructions, and coherence. Blinded reviewers will inspect source passages, while automated checks will supplement their judgments. Ablations will remove persistent claim identities or post-edit support checking. Analysis will examine whether apparent preservation gains result from avoiding requested edits, deleting content, or producing less readable prose.

## Limitations and Conclusion

Claim alignment may fail if revisions substantially reorganize arguments. Source passages might lack context necessary for judging support, and automated checkers could misinterpret qualifications. Thus, human review will remain essential for unresolved cases. The intended contribution is an editing method and evaluation protocol to test citation preservation as continued evidential support across revisions.