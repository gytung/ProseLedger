# Bus Reliability Beyond the Average Wait

## Abstract

A timetable can reduce average waiting time, but may leave some journeys less reliable. We propose to compare a fixed timetable with a holding policy using an anonymized arrival log from one bus route. The study will examine mean waiting time alongside instances of long waits, with peak and off-peak periods reported separately [S2]. A better overall average will not be considered evidence that all passengers benefit.

## Introduction

Passengers may care equally about an unusually long delay and a typical journey. A single average can obscure these differences. The available log records scheduled and observed arrivals on weekdays but includes no passenger identities [S1]. While it supports a comparison of service patterns, it cannot establish how individual passengers experienced those patterns.

## Related Work

The data brief limits the available evidence to a single route and weekday service [S1]. The experimental brief mandates that both policies use the same recorded arrivals [S2]. This comparison will control the input sequence rather than assert that the historical service operated under both policies. Passenger satisfaction is not captured in the source packet.

## Methodology

We will apply the fixed timetable and holding policy to arrivals from 18 weekdays [S2]. Each simulated decision will use only information available at that point in the log. Peak and off-peak periods will be analyzed separately. We will retain instances of service disruption , since removing difficult days could make the policy appear more dependable than it is.

## Planned Evaluation

The planned measures include mean waiting time, the frequency of long waits, and the difference between peak and off-peak outcomes. We will report days when the holding policy performs worse, as well as those where it improves the average. Sensitivity checks will vary the definition of a long wait without selecting the definition that most favours either policy.

## Limitations and Conclusion

A replay of historical arrivals is a limited test of an operational policy, as it does not capture changes in boarding behavior or traffic resulting from a different timetable. Therefore, we will make no causal claim about passenger satisfaction [S2]. The intended result is a clearer comparison of reliability trade-offs on the supplied route, rather than a general guarantee for all bus services.