# Mechanism-based failure analysis

These cases were selected to cover distinct mechanisms, not to estimate their prevalence. All observed events remain in observed_failure_events.json. Most candidate faults were corrected or rolled back before the retained output. Automated auditor findings are distinguished from the constructed known-answer false positive.

## F01 — Unsupported causal link

**Record:** C01 / rules / Limitations and Conclusion

**Original:** A local inventory may also contain outdated boundaries.

**Candidate:** A local inventory might contain outdated boundaries, as no field measurements have been collected for this proposal [S1].

**Finding and cause:** Adds an unsupported causal connection: the absence of field measurements for this proposal does not explain whether the inventory boundaries are outdated. A connective added for fluency can introduce a causal claim absent from the source.

**Action and retained outcome:** The original section was retained. Final manuscript: candidate.

**Next step:** Require each added causal relation to be supported by a source span; otherwise preserve the two statements without a causal connector.

**Evidence:**
- `decoded_audits/C01_rules_audit_sections.json#/reviews/5/issues/1`
- `runs/C01/rules/audit_sections.response.json#/text`
- `runs/C01/rules/revision_ledger.json#/edits/5`
- `decoded_audits/C01_rules_repair_section_findings.json#/sections/0/patches`

## F02 — Modality strengthened

**Record:** C01 / rules / Limitations and Conclusion

**Original:** An abstention rule may make the limits of the evidence clearer while leaving a less complete map.

**Candidate:** An abstention rule may make the limits of the evidence clearer, but it will leave a less complete map.

**Finding and cause:** Changes a possible tradeoff into a definite prediction that the map will be less complete. A possible trade-off becomes a promised consequence.

**Action and retained outcome:** The original section was retained. Final manuscript: candidate.

**Next step:** Compare the scope of modal verbs in addition to surface grammar, and reject unsupported increases in certainty.

**Evidence:**
- `decoded_audits/C01_rules_audit_sections.json#/reviews/5/issues/0`
- `runs/C01/rules/audit_sections.response.json#/text`
- `runs/C01/rules/revision_ledger.json#/edits/5`
- `decoded_audits/C01_rules_repair_section_findings.json#/sections/0/patches`

## F03 — Valid deletion rejected by the repair schema

**Record:** C01 / rules / Limitations and Conclusion

**Original:** An abstention rule may make the limits of the evidence clearer while leaving a less complete map. A local inventory may also contain outdated boundaries. The proposed experiment will therefore not estimate annual retreat rates or establish that any particular glacier is shrinking [S2]. Its contribution would be a more explicit account of what the available images can support.

**Candidate:** An abstention rule may make the limits of the evidence clearer, but it will leave a less complete map. A local inventory might contain outdated boundaries, as no field measurements have been collected for this proposal [S1]. The proposed experiment will not estimate annual retreat rates or establish that any particular glacier is shrinking [S2]. Instead, its contribution will be a more explicit account of what the available images can support.

**Finding and cause:** patch_type The model proposed removing an unsupported clause, but an empty replacement fails the current nonempty-after constraint.

**Action and retained outcome:** The complete patch set was rejected because one replacement was empty. The original section was restored; changes in the other sections remained eligible. Final manuscript: candidate.

**Next step:** Permit deletion patches when a unique exact anchor, coverage bound and post-edit semantic audit all pass; test this change on separate data.

**Evidence:**
- `decoded_audits/C01_rules_repair_section_findings.json#/sections/0/patches`
- `runs/C01/rules/revision_ledger.json#/edits/5/repair`

## F04 — Bias mitigation presented as a guarantee

**Record:** C02 / generic / Methodology

**Original:** We will preserve instances of service disruption, since removing difficult days could make the policy appear more dependable than it is.

**Candidate:** We will retain instances of service disruption to ensure the policy's reliability is accurately reflected.

**Finding and cause:** Retaining disruptions helps avoid an overly favourable assessment but cannot ensure accurate reliability estimates. The revision replaces a qualified bias concern with an unsupported guarantee. Retaining difficult days reduces one selection risk but cannot guarantee accurate reliability estimates.

**Action and retained outcome:** A bounded repair was applied and the revised section was retained after the final automated audit. Final manuscript: candidate.

**Next step:** Preserve the qualified relationship between the procedure and the risk it addresses.

**Evidence:**
- `decoded_audits/C02_generic_audit_sections.json#/reviews/3/issues/0`
- `runs/C02/generic/audit_sections.response.json#/text`
- `runs/C02/generic/revision_ledger.json#/edits/3`
- `decoded_audits/C02_generic_repair_section_findings.json#/sections/0/patches`

## F05 — Grammar worsens during naturalization

**Record:** C02 / rules / Introduction

**Original:** may care as much about an unusually long delay as they do about a typical journey

**Candidate:** may care equally about an unusually long delay as they do about a typical journey

**Finding and cause:** “Equally about ... as they do about” is an awkward comparative construction. Retain “as much about ... as” or use “equally about ... and ...”. The revision combines two incompatible comparative constructions.

**Action and retained outcome:** A bounded repair was applied and the revised section was retained after the final automated audit. Final manuscript: candidate.

**Next step:** Check local grammar independently of lexical simplification; keep the original construction when the change is not an improvement.

**Evidence:**
- `decoded_audits/C02_rules_audit_sections.json#/reviews/1/issues/0`
- `runs/C02/rules/audit_sections.response.json#/text`
- `runs/C02/rules/revision_ledger.json#/edits/1`
- `decoded_audits/C02_rules_repair_section_findings.json#/sections/1/patches`

## F06 — Concrete evaluation safeguard omitted

**Record:** C02 / rules / Planned Evaluation

**Original:** Sensitivity checks will vary the definition of a long wait without selecting the definition that most favours either policy.

**Candidate:** Sensitivity checks will vary the definition of a long wait without favouring either policy.

**Finding and cause:** The revision removes the explicit commitment against selecting the most favourable definition. A general promise of neutrality does not preserve this concrete safeguard against selective reporting. A general promise of neutrality replaces the explicit restriction against selecting a favourable threshold definition.

**Action and retained outcome:** A bounded repair was applied and the revised section was retained after the final automated audit. Final manuscript: candidate.

**Next step:** Represent fixed methodological safeguards as content commitments, not removable stylistic detail.

**Evidence:**
- `decoded_audits/C02_rules_audit_sections.json#/reviews/4/issues/0`
- `runs/C02/rules/audit_sections.response.json#/text`
- `runs/C02/rules/revision_ledger.json#/edits/4`
- `decoded_audits/C02_rules_repair_section_findings.json#/sections/3/patches`

## F07 — Temporal scope altered

**Record:** C03 / rules / Related Work

**Original:** These roles will remain fixed before observation begins.

**Candidate:** These roles will be maintained until observations begin

**Finding and cause:** “Until” implies that the commitment to fixed outcome roles ends when observation begins, weakening the prespecified outcome hierarchy. A rule fixed before observation is rewritten as a rule maintained only until observation starts.

**Action and retained outcome:** A bounded repair was applied and the revised section was retained after the final automated audit. Final manuscript: candidate.

**Next step:** Check temporal connectors as relations, because the same nouns and numbers do not guarantee the same commitment.

**Evidence:**
- `decoded_audits/C03_rules_audit_sections.json#/reviews/2/issues/0`
- `runs/C03/rules/audit_sections.response.json#/text`
- `runs/C03/rules/revision_ledger.json#/edits/2`
- `decoded_audits/C03_rules_repair_section_findings.json#/sections/0/patches`

## F08 — Conservative whole-document rejection

**Record:** C04 / generic / Introduction

**Original:** Tests will check the supplied examples, but passing them will not be presented as proof that a program is correct for every input [S1].

**Candidate:** While tests will verify the supplied examples, passing them does not guarantee the program's correctness for all inputs [S1].

**Finding and cause:** The candidate preserves the limitation of testing but omits the explicit commitment not to present passing tests as proof of correctness for every input. The auditor distinguishes a reporting commitment from a close statement about test limitations; the entire candidate is consequently rejected.

**Action and retained outcome:** The final audit rejected the complete candidate. Under the standard policy, no additional full-audit repair round is allowed; the original manuscript was retained. Final manuscript: original.

**Next step:** Obtain human equivalence labels for borderline cases and calibrate the rejection policy; this observation is a possible over-rejection, not a confirmed false positive.

**Evidence:**
- `runs/C04/generic/checks.json#/audit/issues/0`
- `runs/C04/generic/run.json#/retained`

## F09 — Assessor role changed

**Record:** C05 / rules / Related Work

**Original:** They will not be counted as unnecessary hedging when an editor assesses whether a revision is more concise.

**Candidate:** We will consider these qualifications as integral content and not count them as unnecessary hedging when assessing conciseness.

**Finding and cause:** The revision removes the explicit role of an editor in assessing conciseness and instead assigns the assessment to the authors. Preserve the specified assessor. An editorial simplification shifts the stated assessor from an editor to the study authors.

**Action and retained outcome:** A bounded repair was applied and the revised section was retained after the final automated audit. Final manuscript: candidate.

**Next step:** Preserve who performs each action, especially when review responsibilities are part of the design.

**Evidence:**
- `decoded_audits/C05_rules_audit_sections.json#/reviews/2/issues/0`
- `runs/C05/rules/audit_sections.response.json#/text`
- `runs/C05/rules/revision_ledger.json#/edits/2`
- `decoded_audits/C05_rules_repair_section_findings.json#/sections/0/patches`

## F10 — Controlled comparison overinterpreted

**Record:** C06 / generic / Related Work

**Original:** This isolates the effect of correction from a change in alert policy.

**Candidate:** This design ensures that any changes in alert counts are attributable to the correction process rather than alterations in the alert policy.

**Finding and cause:** The revision strengthens a controlled comparison into a blanket causal guarantee. A fixed threshold rules out threshold changes as an explanation but does not establish that any change in alert counts must result from correction. Holding one factor fixed is rewritten as establishing the sole cause of any observed difference.

**Action and retained outcome:** A bounded repair was applied and the revised section was retained after the final automated audit. Final manuscript: candidate.

**Next step:** Separate the factor controlled by the design from the causal conclusion that the evidence would support.

**Evidence:**
- `decoded_audits/C06_generic_audit_sections.json#/reviews/2/issues/0`
- `runs/C06/generic/audit_sections.response.json#/text`
- `runs/C06/generic/revision_ledger.json#/edits/2`
- `decoded_audits/C06_generic_repair_section_findings.json#/sections/0/patches`

## F11 — Citation scope expanded

**Record:** C06 / generic / Limitations and Conclusion

**Original:** A reference instrument can itself have error, and the study covers only a limited observation period.

**Candidate:** A reference instrument can itself have errors, and the study covers only a limited observation period [S1].

**Finding and cause:** The added citation attributes reference-instrument error and the limited observation period to S1, which states neither. A citation is attached to additional limitations that are not stated in that source packet.

**Action and retained outcome:** A bounded repair was applied and the revised section was retained after the final automated audit. Final manuscript: candidate.

**Next step:** Check the proposition supported by each citation occurrence rather than only whether the identifier is allowed.

**Evidence:**
- `decoded_audits/C06_generic_audit_sections.json#/reviews/5/issues/0`
- `runs/C06/generic/audit_sections.response.json#/text`
- `runs/C06/generic/revision_ledger.json#/edits/5`
- `decoded_audits/C06_generic_repair_section_findings.json#/sections/2/patches`

## F12 — Citation occurrence lost

**Record:** C08 / rules / Planned Evaluation

**Original:** Difficult days will remain in the overall result [S2].

**Candidate:** Difficult days will remain in the overall results.

**Finding and cause:** The revision removes the citation to S2, losing explicit attribution for the requirement to include difficult days in the overall results. A requirement remains in prose but loses its explicit source attribution.

**Action and retained outcome:** A bounded repair was applied and the revised section was retained after the final automated audit. Final manuscript: candidate.

**Next step:** Retain section-level citation occurrence checks and expose the rejection reason in the ledger.

**Evidence:**
- `decoded_audits/C08_rules_audit_sections.json#/reviews/4/issues/0`
- `runs/C08/rules/audit_sections.response.json#/text`
- `runs/C08/rules/revision_ledger.json#/edits/4`
- `decoded_audits/C08_rules_repair_section_findings.json#/sections/0/patches`

## F13 — Dangling modifier introduced

**Record:** C09 / generic / Methodology

**Original:** before the measures are calculated

**Candidate:** before calculating the measures

**Finding and cause:** The implied subject of 'calculating' is the recovered output, creating an awkward modifier. Retain the passive clause or explicitly identify who calculates the measures. The rewritten clause grammatically assigns calculation to the recovered material rather than to the researchers.

**Action and retained outcome:** A bounded repair was applied and the revised section was retained after the final automated audit. Final manuscript: candidate.

**Next step:** Check the actor of a shortened clause; a concise sentence is not automatically a coherent sentence.

**Evidence:**
- `decoded_audits/C09_generic_audit_sections.json#/reviews/3/issues/0`
- `runs/C09/generic/audit_sections.response.json#/text`
- `runs/C09/generic/revision_ledger.json#/edits/3`
- `decoded_audits/C09_generic_repair_section_findings.json#/sections/0/patches`

## F14 — Equivalent numeric wording rejected

**Record:** C02 / component challenge / Methodology

**Original:** arrivals from 18 weekdays

**Candidate:** arrivals from eighteen weekdays

**Finding and cause:** The digit token 18 is absent after a meaning-preserving conversion to eighteen. Changing 18 to eighteen preserves the quantity but removes a digit token. The lexical gate rejects this valid paraphrase even though the semantic auditor accepts it.

**Action and retained outcome:** The deterministic guard rejects the valid paraphrase. The semantic checker accepts it, but their conjunction retains the false rejection. Final manuscript: component challenge; no writing run.

**Next step:** Normalize equivalent number expressions before comparing quantities and retain role-sensitive semantic checks for swapped values.

**Evidence:**
- `semantic_challenges/C02_benign/result.json#/audit`
- `semantic_challenges/C02_benign/result.json#/combinedCorrect`
