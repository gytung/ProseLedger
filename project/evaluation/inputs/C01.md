# When a Glacier Map Is Allowed to Abstain

## Abstract

A glacier outline can change because the ice moved or because the observation is incomplete. We propose to test whether allowing a mapping model to abstain on cloud-covered pixels improves the reliability of boundary comparisons. The study will use two summer visits and a local outline inventory [S1]. It concerns how uncertainty is represented, rather than whether a particular glacier has retreated.

## Introduction

Missing pixels are often inconvenient for a mapping workflow because the output is expected to cover the entire image. Filling every location with a label can nevertheless turn missing evidence into an apparently definite boundary. In this proposal, cloud cover will remain an unavailable observation. The inventory gives a starting outline; it does not by itself provide evidence of recent retreat [S1].

## Related Work

The source packet distinguishes an inventory from a change measurement [S1]. It also defines mandatory classification and abstention as the two conditions to compare [S2]. These definitions motivate a narrow experiment: the image evidence will be held fixed while the output rule changes. We will not use the inventory as an independent reference for the direction of glacier change.

## Methodology

We will provide the same image pairs to a boundary model under both conditions. In the first condition, the model must assign a label to every pixel. In the second, it may abstain where cloud cover makes the observation unavailable. The proposed sample contains 24 image pairs [S2]. Reviewers will examine the resulting boundaries without seeing the condition names.

## Planned Evaluation

The evaluation will report boundary disagreement on observable terrain and the fraction of pixels left unresolved. Abstentions will be reported separately from correct classifications, so the system cannot appear accurate simply by declining most cases. We will also inspect examples in which a cloud edge resembles an ice boundary. These are planned comparisons, and no field measurements are yet available.

## Limitations and Conclusion

An abstention rule may make the limits of the evidence clearer while leaving a less complete map. A local inventory may also contain outdated boundaries. The proposed experiment will therefore not estimate annual retreat rates or establish that any particular glacier is shrinking [S2]. Its contribution would be a more explicit account of what the available images can support.