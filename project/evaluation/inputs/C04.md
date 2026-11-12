# Code Review Suggestions with a Measured Scope

## Abstract

A plausible code review suggestion is useful only if a developer can understand where it applies and what it changes. We propose to compare free-form suggestions with suggestions that identify an exact edit location. Both conditions will receive the same Python function and issue description [S2]. The assistant will propose changes, while a developer will retain authority over acceptance.

## Introduction

General advice can be correct in principle yet difficult to apply to a particular function. Conversely, a precise edit can still alter behaviour in an unintended way. The study therefore separates the location of a suggestion from its correctness. Tests will check the supplied examples, but passing them will not be presented as proof that a program is correct for every input [S1].

## Related Work

The task brief assigns the assistant a supporting role in code review and leaves the final decision with the developer [S1]. The evaluation brief distinguishes free-form suggestions from suggestions anchored to an edit location [S2]. We use these conditions to examine whether specificity helps reviewers assess a proposal, rather than assume that more specific suggestions are necessarily safer.

## Methodology

The planned sample contains 36 small functions [S2]. For each function, both conditions will see identical code and the same short issue description. We will preserve the original tests and record any proposed test changes separately. A suggestion must pass the supplied tests before it can be considered for acceptance, but passing is only one requirement.

## Planned Evaluation

Reviewers will judge whether each suggestion addresses the stated issue, changes unrelated behaviour or leaves an unclear edit location. We will report acceptance alongside test outcomes and review time. A rejected suggestion will remain in the record with its reason. This distinction will allow a passing test result to coexist with a developer decision that the change is unsuitable.

## Limitations and Conclusion

Small functions are easier to inspect than production repositories, and the supplied tests may miss important behaviours. The experiment cannot establish the reliability of autonomous code modification. Its narrower aim is to examine how the form of a suggestion affects developer review while keeping the developer, rather than the assistant or the tests, responsible for the final decision.