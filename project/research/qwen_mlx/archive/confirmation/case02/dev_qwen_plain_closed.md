# Preserving Exploratory Claims Through Claim-Status-Aware Revision

## Abstract

Research proposals integrate established findings, tentative explanations, and planned investigations. Revising these statements for clarity can inadvertently change what authors claim to know. This project proposes a claim-status-aware revision method for cross-disciplinary proposals. The method aims to distinguish evidence-backed premises from hypotheses and planned activities, link factual statements to supplied sources, and examine whether revisions preserve uncertainty and scope. Planned evaluation would assess whether this approach enhances clarity while maintaining exploratory content and avoiding unsupported assertions.

## Introduction

Cross-disciplinary proposals must explain unfamiliar concepts while maintaining room for questions that existing evidence cannot resolve. For instance, a proposal suggests that a mechanism established in one field might operate in another. Removing "might" in a revision can transform an exploratory connection into an asserted finding; deleting the connection can erase the proposal’s motivation. These examples illustrate the problem we are addressing, rather than quantifying its frequency.

The research question is whether explicitly representing claim status can help a revision system preserve exploratory reasoning while enhancing readability. Preservation would encompass the underlying proposition, its level of uncertainty, disciplinary scope, and role in the proposed investigation. Preservation would not require retaining every original phrase or protecting factual errors from correction.

## Related Work

ALCE evaluates citation generation by assessing fluency, correctness, and citation quality, establishing a useful framework for assessing verifiable factual content [S1]. Attribute First, then Generate selects source segments before sentence planning and generation; its authors report more concise attributions and reduced verification time in their evaluated tasks [S2]. These findings motivate evidence mapping but do not demonstrate preservation of exploratory proposal claims.

RefChecker extracts and checks claim-triplets against references [S5], but the proposed project aims to extend this by representing modality and planned activity, which cannot be assessed solely as established factual assertions. Scientific revision research cautions against relying on similarity metrics or automated instruction-following judgments alone, with Jourdan and colleagues reporting that LLM judges struggle with correctness [S4].

## Methodology

The proposed workflow would start with an author-provided draft, source excerpts, and revision instructions. It would identify claim spans and assign provisional roles: factual premises, exploratory hypotheses, planned activities, or other discourse. Mixed statements would be split as feasible. Each claim record would maintain qualifiers, disciplinary context, and links to supporting evidence when applicable.

A revision model would then process these records alongside the draft. Instructions would allow reorganization and clearer phrasing while requiring the preservation of hypothesis status and future tense for planned work. Unsupported factual premises would be flagged for author review. Hypotheses would need explicit exploratory framing, without being treated as source-established findings.

A subsequent comparison would assess original and revised claim records for lost propositions, strengthened certainty, altered scope, and invented support. Ambiguous changes would be presented to authors with the relevant passages. This comparison is a proposed safeguard whose reliability would require evaluation.

## Planned Evaluation

The study would gather permissioned cross-disciplinary proposal excerpts with author-confirmed claim annotations. It would then compare ordinary instruction-based revision, revision with source attribution, and the full proposed workflow under matched editing requests and source access. Disciplinary reviewers would independently assess clarity, preservation of exploratory meaning, factual support, and the feasibility of author review. Targeted measures would count hypothesis deletions, unwarranted certainty increases, scope changes, and unsupported factual additions. Disagreements would be adjudicated and reported. Ablations would remove claim-status annotation or the final comparison to examine their contributions. Analysis would evaluate both benefits and costs, including potential over-hedging or reduced readability, without assuming improvement.

## Limitations and Conclusion

Limitations and challenges include potential overlaps in claim roles and complexities from disciplinary conventions, which could complicate accurate annotation. Supplied excerpts may also leave factual support unresolved. Author involvement would therefore remain necessary. The project aims to determine if explicit claim-status tracking can effectively clarify proposals while retaining the uncertainty necessary for exploratory research.