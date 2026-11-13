# Data card

M5 historical Walmart retail sales, calendar and weekly sell prices, mirrored by Nixtla. Source downloader resolves an immutable Git commit and records SHA256 for archive and extracted CSVs. Only `sales_train_evaluation.csv` and calendar are used for the experiment; hidden test files are never extracted or accessed. `sell_prices.csv` is downloaded but unused to avoid assuming future prices are known.

Nixtla loader reference: https://github.com/Nixtla/datasetsforecast/blob/main/datasetsforecast/m5.py

Mirror: https://github.com/Nixtla/m5-forecasts

Original competition: https://www.kaggle.com/competitions/m5-forecasting-accuracy

Access through a public mirror does not transfer ownership or imply permission for unrestricted redistribution. Raw files are ignored by Git; the repository's code license does not apply to the underlying data. Review the original terms for your intended use. Kaggle account / competition terms may be required when downloading there. Never commit `kaggle.json`.

No actual stock, purchase order, lost demand, lead-time or acquisition cost data is supplied by M5. Such values in the simulator are explicitly hypothetical. Sales may be censored by historical stockouts and assortment changes. Do not present the simulation as observed savings for Walmart or an energy company.
