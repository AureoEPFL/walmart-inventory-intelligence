# Methodology and decision contract

## Intended use

An auditable research prototype for a planner deciding how much to order at a weekly review. The system forecasts **cumulative demand during supplier lead time plus review interval**, not a sum of independently forecast daily quantiles. It compares order-up-to policies under variable lead times and lost sales. It is not a production-certified planner or evidence of performance in petroleum logistics.

## Data and target

M5 records unit sales, not unconstrained demand, actual inventories or supplier lead times. Historical stockouts and assortment availability can censor sales; zeros must not automatically be called zero demand. The experiment treats observed sales as an exogenous demand proxy. In the simulation this proxy is fully observed even when a simulated policy stocks out. No claim is made to estimate the missing historical demand.

Series are selected by a deterministic hash of ID and seed, before inspecting target values. Default: 64 items in CA_1. The larger Kaggle config uses 512. Neither is a full M5 hierarchy benchmark. We do not claim official WRMSSE performance. All sampled series, including sparse/all-zero periods, remain in the study. Early assortment zeros are retained and are a limitation.

## Temporal evaluation

`origin` is the first unobserved day. Demand features use strictly earlier indices. Targets are cumulative sales over `[origin, origin+horizon)`. Targets crossing the end of their partition are excluded. Chronological regions:

1. Training history (up to 730 days).
2. Tuning (63 days), used only to choose each model's number of boosting iterations by early stopping.
3. Calibration (84 days), used to expand prediction intervals.
4. Final test (84 days), not used for model or policy threshold fitting.

After iteration selection, models are refit on training+tuning labels. Models and calibration remain frozen for the final test; historical features update at each rolling origin with newly observed sales. This is rolling-origin evaluation with a frozen model, **not repeated fold retraining or nested cross-validation**. Weekly origins and multiple horizons overlap. Forecast observations therefore are dependent.

## Models

- Seasonal reference: empirical cumulative demand in same-weekday historical blocks, all fully observed at the origin. Mean, median and empirical 10/90 percentiles.
- Global LightGBM Tweedie regression for conditional mean.
- Three global LightGBM quantile regressions (0.1 / 0.5 / 0.9).
- Targets normalized by trailing 28-day mean +1, computed at the origin; predictions converted back to units.
- Historical means, standard deviations, zeros, lags, trend, calendar and static category codes. No future prices, promotions or unobserved demand features. Static item/store metadata is not a target leak.
- Quantile crossing corrected by sorting. Calibration uses nonnegative normalized CQR-style expansion per horizon with a nominal 80% level.

Time dependence, pooling across items and overlapping windows violate exchangeability assumptions. **Calibration does not imply a finite-sample coverage guarantee here.** Report empirical coverage, width, interval score and subgroup failures. The calibrated endpoints are interval bounds, not guaranteed conditional 10th/90th quantiles. Pinball losses on expanded endpoints are descriptive.

## Uncertain lead time and policy

Lead times of 2, 5 and 9 days have probabilities 0.25, 0.5 and 0.25. Weekly review means protection horizons of 9, 12 and 16 days. These are scenario assumptions, not M5 observations.

To mix LightGBM distributions across lead times, inverse-CDF sampling interpolates at probabilities 0, 0.1, 0.5, 0.9 and 1. Support endpoints are 0 and `q90 + max(q90-q50, 1)`. These capped tails are an explicit approximation; risk estimates are not validated tail probabilities. The seasonal mixture uses historical cumulative-demand blocks. Demand/lead dependence is not modeled. Monte Carlo seed is deterministic per origin.

Four fixed policies are evaluated:

1. seasonal_mean: weighted expected protection demand.
2. seasonal_risk: 90th percentile of seasonal mixture.
3. ml_mean: weighted LightGBM mean protection demand.
4. ml_risk: 90th percentile of approximate calibrated ML mixture.

Inventory position = on-hand + on-order. Order quantity = positive target-position gap, rounded up to case pack, then limited by capacity (on-hand + pipeline reserved). Capacity is 42 days of pre-test trailing mean, minimum 10 units. Initial stock is 14 days of that mean, with no initial pipeline.

Simulation order: receipts at start of day; review/order if scheduled; demand fulfillment; lost-sales and end-of-day holding costs. Lead >=1 prevents same-day receipt. Unsatisfied demand is lost, never backlogged. Orders still outstanding at horizon end are reported separately. No procurement/unit revenue is included in the optimization objective: costs are holding, shortage penalty and order setup. They are assumed dollar values, not Walmart economics. No shared supplier capacity, minimum order value, shelf life, substitution or cash limit.

## Fair comparison and uncertainty

Every policy sees identical demand, starting stocks and capacity. Random lead time is indexed by replication × item × calendar day, so policies use common random numbers even if some choose not to order. Default 20 replications, larger config 100.

Paired Monte Carlo intervals summarize cost differences conditional on this demand window and the stipulated lead distribution. They do not include uncertainty over future demand regimes, parameter selection or stores. Coverage observations are not treated as independent confidence trials. Cost sensitivity re-prices the same fixed policies; it does not re-optimize them for each penalty. Retrospective lowest test cost is explicitly exploratory, not a deployed policy selected on untouched evidence.

## Metrics that matter

Forecast: WAPE (mean), RMSE (mean), MAE (median), bias, pinball, nominal-80% coverage, interval width and interval score by horizon.

Operations: unit fill rate (fulfilled/demand), lost units, stockout days, order count, holding/shortage/setup costs, ending on-hand and pipeline. Zero-demand individual items receive fill rate 1; portfolio fill rate uses total fulfilled/total demand.

## Before production

Obtain actual demand, stockout flags, lead-time history and costs; review data licenses and commercial restrictions; define decision ownership and override policy. Run additional temporal/store holdouts, stress tests, supplier-capacity constraints and shadow deployment. Validate calibration under drift and validate business outcomes with planners. Establish monitoring, retraining and rollback. None of those operational approvals is implied by this repository.
