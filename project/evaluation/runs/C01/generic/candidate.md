# When a Glacier Map Is Allowed to Abstain

## Abstract

A glacier outline can change due to ice movement or incomplete observation. We propose testing whether allowing a mapping model to abstain on cloud-covered pixels enhances the reliability of boundary comparisons. The study will utilize two summer visits and a local outline inventory [S1]. The focus is on representing uncertainty rather than determining whether a specific glacier has retreated.

## Introduction

Missing pixels can complicate a mapping workflow, as the output is expected to cover the entire image. Filling every location with a label, however, can transform missing evidence into a seemingly definite boundary. In this proposal, cloud cover will remain an unavailable observation. The inventory provides a starting outline but does not itself establish recent retreat [S1].

## Related Work

The source packet distinguishes between an inventory and a change measurement [S1]. It also defines mandatory classification and abstention as the two conditions to compare [S2]. These definitions motivate a focused experiment: the image evidence remains constant while the output rule varies. We will not use the inventory as an independent reference for the direction of glacier change.

## Methodology

We will provide the same image pairs to a boundary model under both conditions. In the first condition, the model must assign a label to every pixel. In the second condition, it may abstain where cloud cover makes the observation unavailable. The proposed sample includes 24 image pairs [S2]. Reviewers will examine the resulting boundaries without knowing the condition names.

## Planned Evaluation

The evaluation will report boundary disagreement on observable terrain and the fraction of pixels left unresolved. Abstentions will be reported separately from correct classifications so the system cannot appear accurate simply by declining most cases. We will also examine examples where a cloud edge closely resembles an ice boundary. These comparisons are planned, and no field measurements are currently available.

## Limitations and Conclusion

An abstention rule may make the limits of the evidence clearer, albeit at the cost of a less complete map. A local inventory may also contain outdated boundaries. Consequently, the proposed experiment will not estimate annual retreat rates or establish that any particular glacier is shrinking [S2]. Instead, its contribution would be a more explicit account of what the available images can support.