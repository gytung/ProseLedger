# Conditional Editing Experience for Laboratory Handover Notes

## Abstract

This project proposes an editing assistant that learns reusable revision procedures from laboratory handover notes while keeping experiment-specific facts separate. Each stored editing experience would include an applicable condition, an editing operation, and information that must be preserved. The assistant would apply an experience only if the current note and its supporting evidence meet the specified condition. Planned evaluation will assess whether conditional reuse enhances clarity and recipient understanding while maintaining factual content and uncertainty.

## Introduction

Laboratory handover notes may combine completed actions, unresolved problems, and instructions for future work. Effective editing of these notes demands not only clear language but also the precise preservation of distinctions between observations, interpretations, and pending actions. A useful editing procedure can clarify which party is responsible for a task, but it must not introduce an owner unsupported by the evidence.

The research question is whether conditional editing experience can facilitate useful revisions without transferring facts between handovers. We propose storing procedures such as separating an observation from a proposed explanation when both are mentioned in a single sentence. Whether this approach offers advantages over conventional instruction-based editing remains to be empirically determined.

## Related Work

Gao et al. introduce ALCE to evaluate generated text along fluency, correctness, and citation quality, showing that citation support remains incomplete in their evaluated systems [S1]. Slobodkin et al. select source segments before sentence planning and generation; they find that this leads to more concise attributions and reduced verification time in summarization and question answering [S2]. These findings support evidence-linked editing but do not establish its effectiveness for laboratory handovers.

Document revision research highlights the limitations of single-reference approaches [S3]. Jourdan et al. show that language model judges assess instruction-following more effectively than correctness, motivating complementary evaluation methods [S4]. RefChecker evaluates extracted claim-triplets against references [S5]. We would adapt these approaches to examine factual preservation without assuming their performance generalizes to our setting.

## Methodology

We would assemble consented, de-identified handover drafts, supporting records, and editor-approved revisions. Editors would describe the procedural rationale for selected changes. Each experience would contain a trigger condition, an operation, preservation constraints, and a reason to withhold the edit. Stored procedures would exclude sample identities, measurements, and other case-specific facts.

For a new note, the assistant would retrieve candidate experiences and identify relevant evidence spans before proposing changes. For example, an experience could separate completed work from pending work only when their statuses are explicit. If status is ambiguous, the assistant would flag the ambiguity and not make an inference to resolve it. The interface would then present each proposed edit alongside its triggering condition and supporting evidence spans. A verification step would compare original and revised claims, checking quantities, negation, uncertainty, ownership, and temporal status. Users would accept, modify, or reject each suggestion. Accepted edits would be reviewed for procedural scope before becoming candidate experiences.

## Planned Evaluation

We would compare conditional reuse with instruction-only editing and retrieval of prior editing examples without explicit applicability conditions, using the same underlying model and evidence access. Evaluation would separate source sessions across development and testing to reduce overlap.

Blinded laboratory reviewers would assess clarity, actionability, factual preservation, and inappropriate edits. Recipient tasks would measure comprehension and verification time. Condition-mismatch cases would test whether the assistant withholds unsuitable procedures. Ablations would remove condition checking or evidence links. Automated claim checks would supplement expert review; analysis would report uncertainty and examine disagreements rather than treating automated judgments as ground truth.

## Limitations and Conclusion

Incomplete records may prevent reliable verification, and applicability judgments might miss subtle laboratory context. De-identification could remove useful information, and a narrow collection might limit transfer across different laboratories. The proposed assistant aims to support accountable human editing, but its value hinges on demonstrating clearer handovers without introducing unsupported claims or concealing uncertainty.