# Walmart Inventory Intelligence

**A personal research project by Aurélien Laissy.**

## Research question

**Can probabilistic demand forecasts reduce stockouts without carrying excessive inventory when supplier lead times are uncertain?**

I developed this project to study the connection between forecast quality and replenishment decisions. A point forecast estimates expected sales, but ordering decisions also depend on uncertainty, delivery delays, storage capacity and the cost of a lost sale. My analysis compares whether using that uncertainty improves the balance between service and inventory-related costs.

## Walmart sales data

The study uses historical Walmart retail sales released for the **M5 forecasting competition**. Each series records the daily quantity sold for one anonymised product in one store. Product categories include food, household goods and hobbies; commercial product names are not provided.

The completed experiment covers **64 product series from the California store CA_1**, with 1,941 historical days available. The final holdout runs from **29 February to 22 May 2016**. Observed sales are used as a demand proxy. Actual inventory, unfulfilled customer demand, supplier delays and operating costs are not available in these data, so those elements are modelled as explicit assumptions.

## Work completed

- Trained four LightGBM models: expected cumulative demand and the 10th, 50th and 90th percentiles over replenishment horizons.
- Separated training, tuning, interval calibration and final evaluation chronologically, excluding targets that cross split boundaries.
- Built a daily inventory simulator with outstanding orders, variable lead times, storage limits, case-pack constraints and lost sales.
- Compared four replenishment policies using the same historical sales and paired supplier-delay draws.
- Produced an interactive analysis report, item-level order recommendations and cost-sensitivity analysis.

## Results

Results below are averaged over **20 lead-time simulations on the 84-day holdout**. Costs are scenario costs, not observed Walmart expenses.

| Replenishment policy | Mean simulated cost | Unit fill rate |
|---|---:|---:|
| Seasonal mean | $7,344.18 | 81.95% |
| Seasonal with safety stock | $5,403.47 | 92.15% |
| ML mean | $6,787.24 | 84.00% |
| ML with safety stock | $5,039.95 | 94.34% |

Relative to the seasonal safety-stock policy, ML with safety stock produced **6.7% lower simulated costs** and **27.8% fewer unserved units**, improving service by **2.18 percentage points**.

The operational finding is that **the preferred policy depends on the cost of a shortage**. At a $5 penalty per unserved unit, the ML safety-stock policy has the lowest mean cost. At $2, the ML mean policy has the lowest point estimate, although the difference is small. This sensitivity revalues fixed policies; it does not reoptimise them.

At a 12-day horizon, the nominal 80% ML prediction interval covered **82.5%** of observations, versus **67.6%** for the seasonal interval. Better coverage comes with wider intervals and potentially more inventory.

## Interpretation and limits

These are retrospective results from one store and one held-out period, not realised savings or work commissioned by Walmart. Historical stockouts may censor observed sales. The simulation uses assumed starting stocks, capacities, costs and lead-time probabilities. Its approximate demand-distribution tails and time-dependent calibration do not provide guaranteed future stockout probabilities.

The next research steps are evaluation across additional stores and periods, and comparison of policies at matched service levels. The larger Kaggle configuration is available in the code but was not used for the reported results.

## Research record

- [Methodology](docs/METHODOLOGY.md)
- [Results discussion, French](docs/INSIGHTS_FR.md)
- [Measured metrics and experiment manifest](docs/results)
- [Data description](docs/DATA_CARD.md) and [model specification](docs/MODEL_CARD.md)
- [Operational decision logic](docs/OPERATIONS.md)

**Implementation:** Python, LightGBM, NumPy, pandas and Plotly. Ten automated tests cover temporal leakage, inventory conservation, pipeline accounting and model persistence. Training code, local/Kaggle configurations and the analysis notebook are included. Raw data, local environments and trained run artifacts are excluded from this repository. Technical execution notes are in [docs/TECHNICAL_NOTES.md](docs/TECHNICAL_NOTES.md).
