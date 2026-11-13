# Model card

**Status:** personal research prototype. Actual measured results are generated per run in `SUMMARY.md`, `forecast_metrics.csv` and `policy_metrics.csv`. No production-grade performance claim.

**Training:** four global LightGBM boosters (mean and quantiles), frozen chronological final holdout. Saved as UTF-8 text, not pickle. `schema.json` records feature order, category mappings, calibration and iteration counts. `manifest.json` records exact environment, source-code hashes, data SHA256, dates and config.

**Input:** validated nonnegative daily sales panel, continuous calendar, static product/store categories. Prediction requires at least 56 observed days. Unknown category mappings require a controlled rebuild; do not silently remap codes at deployment.

**Outputs:** nonnegative mean/median, sorted interval bounds for cumulative demand, simulated target inventories, capacity-constrained order quantities and a protection-demand exceedance proxy. The proxy is not a validated probability of an actual stockout with intermediate receipts.

**Appropriate:** reproducible demand forecasting experiments; demonstrating how uncertainty affects reorder policies; analysis of measured cost and service trade-offs.

**Inappropriate:** autonomous live procurement; petroleum physical planning; use with unreviewed costs, censored demand or materially shifted lead times.

**Known weaknesses:** sales censoring; deterministic sub-sampling; global calibration can hide segment failures; approximate capped tails; no dependence between supplier delays and demand; frozen model may drift; finite inventory horizon and assumed costs. Aggregate gain feature importance is descriptive, not causal attribution.

**Expected monitoring:** feature freshness, missing dates, negative quantities, category changes, demand drift, signed bias, rolling interval coverage by segment/horizon, realized lead distribution, fill rate and planner override frequency. Alert thresholds must be selected with the business rather than inferred from this demo.
