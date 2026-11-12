# Evidence-Led Revision of Scientific Reviewer Responses

## Abstract

Revising responses to scientific peer reviewers requires clear argumentation without changing what the authors can substantiate. We propose an evidence-led revision workflow that links substantive response claims to supplied manuscript passages, experiment records, and author-approved plans. The workflow will distinguish completed work from proposed actions and flag unsupported statements for author review. Planned evaluation will assess factual support, reviewer-request coverage, readability, and verification effort against direct revision baselines.

## Introduction

A reviewer response may explain an existing result, report a manuscript change, acknowledge a limitation, or promise additional work. These statements carry different evidential requirements. A fluent rewrite can become misleading if it strengthens a conclusion or describes an intended experiment as completed. Improving expression therefore requires preserving both claim content and action status.

This project asks whether organizing evidence before revision can improve support preservation while retaining useful editorial changes. The proposed contribution is a response-specific workflow that makes evidence gaps visible and keeps the author responsible for resolving them. Its effectiveness remains an empirical question.

## Related Work

ALCE evaluates cited generation through fluency, correctness, and citation quality, and its authors report substantial remaining gaps in citation support [S1]. These findings motivate separate assessment of writing quality and evidential grounding; they do not establish performance on reviewer responses.

Attribute First, then Generate selects source segments before sentence planning and generation. Its authors report concise attributions and reduced human verification time in summarization and long-form question answering [S2]. We propose adapting this ordering to response revision. TETRA addresses document-level academic revision, including coherence and consistency [S3]. Scientific revision evaluation research also reports that LLM judges struggle with correctness, motivating complementary assessment methods [S4]. RefChecker provides a further precedent for extracting claims and checking them against references [S5]. None of the supplied excerpts establishes that these methods preserve commitments in reviewer correspondence.

## Methodology

The workflow will receive reviewer comments, a draft response, and an author-supplied evidence package. It will first decompose each comment into actionable requests and map existing response passages to them.

Next, it will construct an evidence ledger. Each substantive claim will have a supporting passage, an evidence category, and an action status: existing finding, documented completed change, proposed action, or unresolved assertion. A statement that an experiment was performed will require a corresponding record; an intention alone will support only prospective wording. Requests without sufficient evidence will remain explicitly unresolved.

The revision stage will use this ledger to plan and rewrite response paragraphs. It may improve organization, clarity, and tone while preserving qualifications and linking factual statements to concise evidence spans in an accompanying author-facing view. A subsequent checker will compare revised claims with their evidence and original status. Flagged passages will return to the author for resolution, with proposed wording clearly separated from verified support.

## Planned Evaluation

We will assemble consented or publicly available response materials with suitable evidence records. Comparisons will include direct language-model revision and revision given the same evidence without an explicit ledger. Ablations will remove evidence-first planning or action-status labels separately.

Blinded assessors will judge claim support, preservation of uncertainty and commitments, reviewer-request coverage, and readability. Verification time and unresolved-claim detection will measure practical usefulness. Automatic checks will supplement human judgments rather than determine correctness alone, following the evaluation concerns in [S4]. Analysis will distinguish incomplete evidence, incorrect evidence matching, and unsupported rewriting. All comparisons remain planned, without assumed gains.

## Limitations and Conclusion

Incomplete records may leave valid statements unverifiable, while automated claim extraction may miss qualifications or implicit commitments. Expert assessment will also require time and domain knowledge. The project will test whether explicit evidence organization helps authors revise reviewer responses clearly while preserving the boundaries of their findings and planned work.