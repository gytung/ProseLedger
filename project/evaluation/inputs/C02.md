# Bus Reliability Beyond the Average Wait

## Abstract

A timetable can lower average waiting time while leaving some journeys less reliable. We propose to compare a fixed timetable with a holding policy using an anonymized arrival log from one bus route. The study will examine mean waiting time alongside long waits, with peak and off-peak periods reported separately [S2]. A better overall average will not be treated as evidence that all passengers benefit.

## Introduction

Passengers may care as much about an unusually long delay as they do about a typical journey. A single average can hide these differences. The available log records scheduled and observed arrivals on weekdays but includes no passenger identities [S1]. It can support a comparison of service patterns, although it cannot establish how individual passengers experienced those patterns.

## Related Work

The data brief limits the available evidence to one route and to weekday service [S1]. The experimental brief requires both policies to use the same recorded arrivals [S2]. This comparison will control the input sequence rather than claim that the historical service operated under both policies. Passenger satisfaction is outside the information recorded in the source packet.

## Methodology

We will apply the fixed timetable and holding policy to arrivals from 18 weekdays [S2]. Each simulated decision will use only information available at that point in the log. Peak and off-peak periods will remain separate throughout analysis. We will preserve instances of service disruption, since removing difficult days could make the policy appear more dependable than it is.

## Planned Evaluation

The planned measures are mean waiting time, the frequency of long waits and the difference between peak and off-peak outcomes. We will report days on which the holding policy performs worse as well as those on which it improves the average. Sensitivity checks will vary the definition of a long wait without selecting the definition that most favours either policy.

## Limitations and Conclusion

A replay of historical arrivals is a limited test of an operational policy. It does not capture changes in boarding behaviour or traffic caused by a different timetable. We will therefore make no causal claim about passenger satisfaction [S2]. The intended result is a clearer comparison of reliability trade-offs on the supplied route, not a general guarantee for all bus services.