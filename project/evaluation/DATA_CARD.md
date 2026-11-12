# Controlled manuscript challenge

**Purpose.** Assess whether an editing procedure improves prose while preserving a fixed set of scientific commitments. The collection supports paired comparisons and inspectable failure analysis; it is not a benchmark of human versus machine authorship.

**Composition.** Twelve newly constructed English research proposals, each with the same six section headings, two short source packets and six reference facts. Topics cover glacier mapping, transport, plant growth, code review, museum descriptions, water sensors, oral history, energy forecasting, recycling, accessible routes, educational feedback and archaeological interpretation. The reference facts cover quantities, roles, attribution, uncertainty, exclusions, temporal boundaries and logical conditions.

**Source status.** The source packets are controlled design briefs authored for this evaluation. Their `[S1]` and `[S2]` identifiers refer to those packets, not to external papers. They describe proposed studies and do not assert that the studies were performed. No participant data, clinical records or private research data are included.

**Reference labels.** Each proposal includes six statements whose preservation can be checked against the packet and original. The mutation challenge then changes one explicit statement at a time. Its 12 invalid edits alter a known commitment; its 12 valid edits preserve meaning. Both before/after strings and the reason for each label are distributed. These labels establish source-relative correctness, not external scientific truth.

**Selection and separation.** All 12 inputs were frozen before writing-model inference, with hashes in `freeze.json`. No case was selected or removed based on the resulting prose, detector probability or model preference. The data are separate from the earlier four-case MLX cohort and earlier development records. Their controlled construction limits claims of population generalization.

**Measurements.** The test distributes exact drafts, both raw and retained revisions, verification traces, model usage, pairwise judgments in both display orders and post-generation detector results. Automated judgments remain distinct from human evaluation. Every failure and unchanged output is retained.

**Reuse.** Reproduce the supplied input hashes and pinned writer condition before comparing results. If models, quantization, runtime or prompts change, report the new condition separately. Do not use the 24 mutation examples as tuning data and then describe performance on the same examples as held-out accuracy.
