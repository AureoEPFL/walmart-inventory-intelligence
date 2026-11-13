# From forecasts to a replenishment decision

An inventory planner answers: which items require attention, how much should we order, when will it arrive, and what does the safety stock cost?

1. Start with available stock, confirmed open orders, supplier lead times, physical capacity and pack sizes.
2. Forecast cumulative sales over the protection period. A weekly review and a five-day lead require twelve days of coverage.
3. Compare a mean-demand target with a safety-stock target. High service is not free: it ties up storage and capital.
4. Subtract inventory position (on hand + outstanding orders). Check capacity and round to purchase packs.
5. Escalate a risk that an ordinary order cannot solve: expedite with procurement, substitute with commercial teams, or reallocate between warehouses. These options are not implemented in the current simulator.

## Inventory snapshot interface

Create a CSV with one row per selected series and columns `series,onhand,pipeline,capacity`. Use the identifiers in a run's `selected_series.csv`. Quantities must be nonnegative; capacity must cover current on-hand plus reserved pipeline. Pipeline is assumed confirmed; its individual arrival dates are not represented in this snapshot recommendation.

```powershell
.\.venv\Scripts\python.exe scripts/recommend.py --run runs/local-v3 --data data/raw --stock my-stock.csv --output my-orders.csv
```

The tool reloads saved models and outputs a capacity-constrained ML safety-stock order. It refuses mismatched series. It does not place orders or modify stock. The remaining exposure before deliveries requires arrival-date-aware scheduling beyond this snapshot tool.

## Operational research questions

- Does better average forecast accuracy actually lower inventory cost?
- How much additional service do we buy with safety stock?
- Which product categories drive shortages, and are the intervals too narrow for them?
- Does the preferred policy change if a lost sale is twice as expensive?
- Would shortening supplier delays outperform further model tuning?

Inspect `policy_metrics.csv`, `paired_comparisons.csv`, `cost_sensitivity.csv` and per-SKU `inventory_runs.parquet`. Comparisons on the final holdout are exploratory; selecting and deploying a policy requires a separate prospective validation.

## Before real deployment

Replace sales-only demand with demand and historical availability; integrate dated open orders and supplier records; estimate actual holding/lost-margin costs; validate promotions and assortment changes; monitor interval coverage and service; run a shadow trial before any purchasing automation.
