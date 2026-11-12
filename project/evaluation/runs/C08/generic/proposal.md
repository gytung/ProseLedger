# Energy Forecasts with a Fixed Information Cutoff

## Abstract

An energy forecast may appear accurate if it incorporates information unavailable at the time of prediction. We propose comparing a seasonal baseline with a learned forecaster for next-day demand in a single campus building. Both models will use the same information cutoff [S2]. The experiment will prioritize deployable forecasting conditions over the best fit to a completed record.

## Introduction

A weather reading collected after a forecast deadline can explain demand retrospectively but cannot support the earlier prediction. The task brief excludes such observations [S1] and represents occupancy through a published timetable, without tracking individuals. These restrictions define the information available to the forecaster and will remain unchanged when the two methods are compared.

## Related Work

The source packet specifies one building as the unit of analysis and next-day demand as the target [S1]. The evaluation brief requires a shared information cutoff and a held-out period [S2]. This design is not interpreted as a study of household electricity use. Instead, the comparison assesses whether a more flexible model adds value under the same practical information limits.

## Methodology

The evaluation will span 42 consecutive days, with the final 14 days held out from the fitting process [S2]. Features will be assembled as they would have been available at each forecast deadline. Both the seasonal baseline and the learned forecaster will receive the same eligible observations. Missing inputs will be recorded rather than replaced with measurements obtained later.

## Planned Evaluation

We plan to report forecast errors for each evaluation day and separately inspect unusually hot days. Difficult days will remain included in the overall results [S2]. The report will also identify forecasts that lacked an eligible weather observation. This distinction ensures that missing-input failures are distinguishable from model errors on fully observed inputs, without excluding either from the record.

## Limitations and Conclusion

A short series from one building cannot establish performance across seasons or sites. Additionally, a learned model may offer little improvement over a seasonal baseline under a strict information cutoff. The study will report such outcomes if they occur. Its central requirement is a fair comparison based on information available at prediction time, rather than a retrospective explanation of demand.