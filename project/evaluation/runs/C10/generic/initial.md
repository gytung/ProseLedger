# Accessible Routes without Assuming Accessible Doors

## Abstract

A route can avoid steps and still end at a door that a traveller cannot use. We propose to test a campus routing interface that distinguishes a step-free path from a verified accessible destination. A verified route will require evidence for both the path and the entrance [S2]. Missing door measurements will remain visible as unknown information.

## Introduction

A single accessibility label can conceal which part of a journey has actually been checked. The available campus map records paths and entrances, but some door measurements are absent [S1]. Treating an unmeasured door as usable would make the map more complete at the cost of an unsupported claim. The interface should help users see this gap before they begin a trip.

## Related Work

The task brief explicitly separates path properties from entrance properties [S1]. The evaluation brief defines verification as the conjunction of both requirements [S2]. We will preserve that distinction in route descriptions. A step-free path may be reported as such, but it will not automatically receive the stronger label of a verified accessible route.

## Methodology

We plan to test 32 origin-destination pairs [S2]. For each pair, the system will retrieve the path record and destination entrance record. It will mark the route verified only if both meet the recorded requirements. An unknown entrance will be displayed separately, together with the missing measurement, rather than silently placed among the verified options.

## Planned Evaluation

Evaluation will compare the displayed route status against the supplied records. We will report unsupported verification labels, correctly identified unknown entrances and the clarity of the explanation shown to users. A hard case will have a step-free path but no usable entrance evidence. Success requires preserving this distinction, not merely finding a path through the map.

## Limitations and Conclusion

The records may become outdated, and accessibility needs differ between users. The study cannot guarantee that a route will be suitable for every traveller. It will also make no inference about unmeasured doors [S2]. The proposed contribution is a clearer representation of which journey components are supported by the available records and which still need checking.