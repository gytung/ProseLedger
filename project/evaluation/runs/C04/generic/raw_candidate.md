# Code Review Suggestions with a Measured Scope

## Abstract

A plausible code review suggestion must be clear and actionable for a developer to understand where it applies and what changes are proposed. We propose comparing free-form suggestions with those that specify an exact edit location. Both conditions will receive the same Python function and issue description [S2]. The assistant will propose changes, while the developer retains authority over acceptance.

## Introduction

General advice, while potentially correct in principle, can be challenging to apply to a specific function. Conversely, a precise edit might still alter behavior in an unintended manner. This study, therefore, separates the location of a suggestion from its correctness. While tests will verify the supplied examples, passing them does not guarantee the program's correctness for all inputs [S1].

## Related Work

The task brief assigns the assistant a supporting role in code review, leaving the final decision with the developer [S1]. The evaluation brief distinguishes between free-form suggestions and those anchored to an exact edit location [S2]. We use these conditions to examine whether specificity aids reviewers in assessing a proposal, rather than assuming that more specific suggestions are inherently safer.

## Methodology

The planned sample consists of 36 small functions [S2]. For each function, both conditions will receive identical code and the same short issue description. The original tests will be preserved, and any proposed test changes will be recorded separately. A suggestion must pass the supplied tests to be considered for acceptance, but passing is only one requirement.

## Planned Evaluation

Reviewers will evaluate each suggestion to determine if it addresses the stated issue, modifies unrelated behavior, or leaves an unclear edit location. We will report the acceptance of each suggestion alongside test outcomes and review time. Rejected suggestions will be recorded with their reasons. This distinction ensures that a passing test result can coexist with a developer decision to reject the change.

## Limitations and Conclusion

Small functions are easier to inspect than production repositories, and the supplied tests may overlook important behaviors. The experiment cannot establish the reliability of autonomous code modification; its primary aim is to examine how the form of a suggestion affects developer review, with the developer retaining the final decision.