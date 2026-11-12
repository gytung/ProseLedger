# Code Review Suggestions with a Measured Scope

## Abstract

A plausible code review suggestion is useful only if a developer can understand where it applies and what it changes. We propose comparing free-form suggestions with those that identify an exact edit location. Both conditions will receive the same Python function and issue description [S2]. The assistant will propose changes, while a developer retains authority over acceptance.

## Introduction

General advice can be correct in principle but difficult to apply to a specific function. Conversely, a precise edit might still alter behavior in an unintended way. The study therefore distinguishes the location of a suggestion from its correctness. Tests will check the supplied examples, but passing them will not be presented as proof that the program is correct for every input [S1].

## Related Work

The task brief assigns the assistant a supporting role in code review, leaving the final decision with the developer [S1]. The evaluation brief distinguishes free-form suggestions from those anchored to an exact edit location [S2]. We use these conditions to examine whether specificity aids reviewers in assessing a proposal, rather than assuming that more specific suggestions are inherently safer.

## Methodology

The planned sample includes 36 small functions [S2]. For each function, both conditions will receive identical code and the same short issue description. We will retain the original tests and separately record any proposed test changes. A suggestion must pass the supplied tests to be considered for acceptance, but passing is only one requirement.

## Planned Evaluation

Reviewers will evaluate each suggestion to determine if it addresses the stated issue, changes unrelated behaviour, or leaves an unclear edit location. We will report the acceptance of each suggestion alongside test outcomes and review time. Rejected suggestions will be recorded with their reasons. This distinction allows a passing test result to coexist with a developer decision that the change is unsuitable.

## Limitations and Conclusion

Small functions are easier to inspect than production repositories, and the supplied tests may miss important behaviors. While the experiment cannot establish the reliability of autonomous code modification, its narrower aim is to examine how the form of a suggestion affects developer review, with the developer retaining the final decision.