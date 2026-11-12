# Preserving Exploratory Claims Through Claim-Status-Aware Revision

## Abstract

Research proposals combine established findings, tentative explanations, and planned investigations. Revising these statements for clarity can inadvertently change what authors claim to know. This project proposes a claim-status-aware revision method for cross-disciplinary proposals. The method would distinguish evidence-backed premises from hypotheses and planned activities, link factual statements to supplied sources, and examine whether revisions preserve uncertainty and scope. Planned evaluation would assess whether this structure improves clarity while retaining exploratory content and avoiding unsupported assertions.

## Introduction

Cross-disciplinary proposals must explain unfamiliar concepts while leaving room for questions that existing evidence cannot settle. Consider a proposal suggesting that a mechanism established in one field might operate in another. A revision that removes “might” can turn an exploratory connection into an asserted finding; deleting the connection can erase the proposal’s motivation. These examples define the problem investigated here, rather than establish how frequently it occurs.

The research question is whether explicitly representing claim status can help a revision system preserve exploratory reasoning while improving readability. Preservation would concern the underlying proposition, its uncertainty, disciplinary scope, and role in the proposed investigation. It would not require retaining every original phrase or protecting factual errors from correction.

## Related Work

ALCE evaluates citation generation through fluency, correctness, and citation quality, establishing a useful framework for assessing verifiable factual content [S1]. Attribute First, then Generate selects source segments before sentence planning and generation; its authors report more concise attributions and reduced verification time in their evaluated tasks [S2]. These findings motivate evidence mapping but do not demonstrate preservation of exploratory proposal claims.

RefChecker extracts claim-triplets and checks them against references [S5]. The proposed project would extend this general checking perspective by representing modality and planned activity, which cannot be assessed solely as established factual assertions. Scientific revision research also cautions against relying on similarity metrics or automated instruction-following judgments alone: Jourdan and colleagues report that LLM judges struggle with correctness [S4].

## Methodology

The proposed workflow would begin with an author-provided draft, source excerpts, and revision instructions. It would identify claim spans and assign provisional roles: factual premise, exploratory hypothesis, planned activity, or other discourse. Mixed statements would be split where feasible. Each claim record would retain qualifiers, disciplinary context, and links to supporting evidence when applicable.

A revision model would then receive these records alongside the draft. Instructions would permit reorganization and clearer phrasing while requiring preservation of hypothesis status and future tense for planned work. Unsupported factual premises would be flagged for author review. Hypotheses would require explicit exploratory framing, without being treated as source-established findings.

A subsequent comparison would inspect original and revised claim records for lost propositions, strengthened certainty, altered scope, and invented support. Ambiguous changes would be presented to authors with the relevant passages. This comparison is a proposed safeguard whose reliability would itself require evaluation.

## Planned Evaluation

The study would assemble permissioned cross-disciplinary proposal excerpts with author-confirmed claim annotations. It would compare ordinary instruction-based revision, revision with source attribution, and the full proposed workflow under matched editing requests and source access.

Disciplinary reviewers would independently assess clarity, preservation of exploratory meaning, factual support, and feasibility of author review. Targeted measures would count hypothesis deletions, unwarranted certainty increases, scope changes, and unsupported factual additions. Disagreements would be adjudicated and reported. Ablations would remove claim-status annotation or the final comparison to examine their respective contributions. Analysis would consider both benefits and costs, including excessive hedging or reduced readability, without presuming improvement.

## Limitations and Conclusion

Claim roles can overlap, and disciplinary conventions may complicate annotation. Supplied excerpts may also leave factual support unresolved. Author involvement would therefore remain necessary. The project would test whether explicit claim-status tracking offers a practical way to clarify proposals while preserving the uncertainty that makes exploratory research possible.