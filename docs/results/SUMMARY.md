# Measured run: local-v3

- Real M5 retail sales: 64 sampled series, store CA_1.
- Training/tuning/calibration/test are chronological and target-purged.
- Lowest simulated mean cost in this run: **ml_risk**, $5,039.95; unit fill rate 94.34%.
- This is a retrospective comparison, not an independently validated policy selection. No claim that ML necessarily beats the seasonal baseline.
- Costs, starting stocks, capacity and lead times are assumptions. M5 has sales, not observed inventory or unmet demand.
- Monte Carlo intervals condition on this fixed demand history. They do not quantify all model/data uncertainty.

## Policy results

policy,mean_cost,cost_mc95_low,cost_mc95_high,fill_rate,lost_units,holding_cost,ordering_cost,ending_onhand,ending_pipeline

ml_mean,6787.2435,6721.628141923607,6852.858858076393,0.8399683488658344,910.1,1178.4434999999999,1058.3,410.4,83.6

ml_risk,5039.9515,4960.033504138361,5119.869495861639,0.9433620538069281,322.1,2268.1515,1161.3,924.9,96.3

seasonal_mean,7344.1845,7276.912250209704,7411.456749790296,0.8195357833655706,1026.3,1083.4845,1129.2,413.9,82.3

seasonal_risk,5403.464999999998,5339.651039326418,5467.278960673579,0.9215227712326358,446.3,1914.1650000000002,1257.8,805.0,93.7


## Paired differences versus seasonal_mean

policy,mean_cost_difference,paired_mc95_low,paired_mc95_high

ml_mean,-556.941,-606.2782869633028,-507.60371303669723

ml_risk,-2304.233,-2380.282478282132,-2228.183521717868

seasonal_mean,0.0,0.0,0.0

seasonal_risk,-1940.7195000000004,-1994.1289232302129,-1887.3100767697879


## Operational interpretation

1. Compare seasonal_risk and ml_risk at similar service levels, not just mean forecast error.
2. Inspect interval coverage by horizon; calibration is measured, not presumed.
3. Use cost_sensitivity.csv to explain how the preferred policy changes with shortage cost.
4. Explain why all four policies see the same demand and lead-time random numbers.
5. The recommendation snapshot uses hypothetical starting stock, not Walmart's actual inventory.
