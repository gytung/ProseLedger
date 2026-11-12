# Conditional Editing Experience for Laboratory Handover Notes

## Abstract

This project proposes an editing assistant that learns reusable revision procedures from laboratory handover notes while keeping experiment-specific facts separate. Each stored editing experience would specify an applicable condition, an editing operation, and information that must be preserved. The assistant would apply an experience only when the current note and its supporting evidence satisfy that condition. Planned evaluation would examine whether conditional reuse improves clarity and recipient understanding while preserving factual content and uncertainty.

## Introduction

Laboratory handover notes may combine completed actions, unresolved problems, and instructions for subsequent work. Editing such notes requires more than fluent wording: a revision must preserve distinctions between observations, interpretations, and pending actions. A useful editing procedure might clarify who should perform a task, but it must not supply an owner absent from the evidence.

The research question is whether conditional editing experience can support useful revisions without transferring facts between handovers. We propose storing procedures such as separating an observation from a proposed explanation when both appear in one sentence. Whether this approach offers advantages over ordinary instruction-based editing remains an empirical question.

## Related Work

Gao et al. introduce ALCE to evaluate generated text along fluency, correctness, and citation quality, demonstrating that citation support remains incomplete in their evaluated systems [S1]. Slobodkin et al. select source segments before sentence planning and generation; they report more concise attributions and reduced verification time in summarization and question answering [S2]. These findings motivate evidence-linked editing, but do not establish effectiveness for laboratory handovers.

Document revision research also challenges reliance on a single reference revision [S3]. Jourdan et al. report that LLM judges assess instruction-following more effectively than correctness, motivating complementary evaluation methods [S4]. RefChecker assesses extracted claim-triplets against references [S5]. We would adapt these ideas to examine factual preservation, without assuming their reported performance transfers to this setting.

## Methodology

We would assemble consented, de-identified handover drafts, supporting records, and editor-approved revisions. Editors would describe the procedural rationale for selected changes. Each experience would contain a trigger condition, an operation, preservation constraints, and a reason to withhold the edit. Stored procedures would exclude sample identities, measurements, and other case-specific facts.

For a new note, the assistant would retrieve candidate experiences and identify relevant evidence spans before proposing changes. For example, an experience could separate completed work from pending work only when their statuses are explicit. If status is ambiguous, the assistant would flag the ambiguity instead of resolving it through inference.

The interface would present each proposed edit alongside its triggering condition and supporting spans. A verification step would compare original and revised claims, checking quantities, negation, uncertainty, ownership, and temporal status. Users would accept, modify, or reject each suggestion. Accepted edits would become candidate experiences only after their procedural scope was reviewed.

## Planned Evaluation

We would compare conditional reuse with instruction-only editing and retrieval of prior editing examples without explicit applicability conditions, using the same underlying model and evidence access. Evaluation would separate source sessions across development and testing to reduce overlap.

Blinded laboratory reviewers would assess clarity, actionability, factual preservation, and inappropriate edits. Recipient tasks would measure comprehension and verification time. Condition-mismatch cases would test whether the assistant withholds unsuitable procedures. Ablations would remove condition checking or evidence links. Automated claim checks would supplement expert review; analysis would report uncertainty and examine disagreements rather than treating automated judgments as ground truth.

## Limitations and Conclusion

Incomplete records may prevent reliable verification, and applicability judgments may miss subtle laboratory context. De-identification could also remove useful information, while a narrow collection may limit transfer across laboratories. The proposed assistant would therefore support accountable human editing. Its value would depend on demonstrating clearer handovers without introducing unsupported claims or concealing uncertainty.