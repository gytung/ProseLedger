# Energy Forecasts with a Fixed Information Cutoff

## Abstract

An energy forecast can look accurate if it uses information that would not have been available when the prediction was needed. We propose to compare a seasonal baseline with a learned forecaster for next-day demand in one campus building. Both will use the same information cutoff [S2]. The experiment will focus on deployable forecasting conditions rather than the best fit to a completed record.

## Introduction

A weather reading collected after a forecast deadline may explain demand retrospectively but cannot support that earlier prediction. The task brief excludes such observations [S1]. It also represents occupancy through a published timetable, without tracking individuals. These restrictions define the information available to the forecaster and will remain unchanged when the two methods are compared.

## Related Work

The source packet specifies one building as the unit of analysis and next-day demand as the target [S1]. The evaluation brief requires a shared cutoff and a held-out period [S2]. We will not interpret this design as a study of household electricity use. The comparison instead asks whether a more flexible model adds value under the same practical information limits.

## Methodology

The evaluation will cover 42 consecutive days, with the final 14 days held out from fitting [S2]. Features will be assembled as they would have been available at each forecast deadline. The seasonal baseline and learned forecaster will receive the same eligible observations. We will record missing inputs rather than silently replace them with measurements obtained later.

## Planned Evaluation

We plan to report forecast errors for every evaluation day and to inspect unusually hot days separately. Difficult days will remain in the overall result [S2]. The report will also state which forecasts lacked an eligible weather observation. This makes a missing-input failure distinguishable from a model error on a fully observed input, without discarding either from the record.

## Limitations and Conclusion

A short series from one building cannot establish performance across seasons or sites. A learned model may also offer little improvement over a seasonal baseline under a strict information cutoff. The study will report that outcome if it occurs. Its central requirement is a fair comparison based on information available at prediction time, not a retrospective explanation of demand.