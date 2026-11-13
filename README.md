# Walmart Inventory Intelligence

**Question de recherche : comment réduire les ruptures sans surstocker lorsque la demande et les délais fournisseurs sont incertains ?**

Cas d'étude indépendant sur des ventes historiques Walmart. Le responsable approvisionnement doit décider chaque semaine combien commander : trop peu entraîne des ventes perdues, trop immobilise du stock. Nous testons si prévoir une distribution de demande, plutôt qu'une simple moyenne, améliore cet arbitrage.

**Comprendre les données :** M5 est le nom du concours de prévision qui a diffusé ces historiques Walmart. Une série représente les quantités vendues chaque jour pour un produit dans un magasin. Les produits portent des identifiants anonymisés, pas des noms commerciaux. Notre essai utilise 64 références du magasin californien anonymisé `CA_1`, avec 1 941 jours d'historique disponibles. Le test final couvre le 29 février au 22 mai 2016. Les ventes sont observées ; les stocks, délais fournisseurs et coûts sont des scénarios simulés. Le modèle ne connaît donc pas les véritables ruptures historiques de Walmart.

**Résultat du premier essai :** comparé à une politique saisonnière avec stock de sécurité, le ML avec sécurité réduit le coût simulé de **6,7 %** et les unités non servies de **27,8 %**, pour un taux de service en unités passant de **92,15 % à 94,34 %**. Comparaison sur 84 jours et 20 tirages de délais ; résultat conditionnel aux hypothèses, pas une économie réalisée chez Walmart.

**Predict demand. Understand stockout exposure. Decide when and how much to order.**

A reproducible ML and operations research portfolio project using real M5 retail sales. Four trainable LightGBM models forecast the mean and demand quantiles over replenishment horizons. A discrete-time inventory simulator compares four ordering policies under variable supplier delays, capacity constraints and lost sales.

This is a research prototype with an executable evaluation protocol, not a production-certified system. Retail sales are not diesel demand; inventory, delays and costs are explicitly simulated.

## Run locally

Python 3.11 or 3.12 recommended. From this directory on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe scripts/download_m5.py --commit 72b8e7fd3b565b3c538adcb1d1a05117d8562d7e
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m inventory_intelligence.cli --config configs/local.json --output runs/my-first-run
Start-Process runs/my-first-run/report.html
```

On Linux/macOS use `.venv/bin/python`. Each run requires a new output directory, preventing accidental overwrites. No API key is needed for the public Nixtla mirror. `requirements-lock.txt` records the environment used for the first experiment.

## What you get

- An offline interactive HTML report: cost/service comparison, interval coverage, forecast error, stock trajectory, SKU selector and shortage-cost sensitivity.
- Mean and 10th/50th/90th percentile LightGBM models, saved as portable text, reloadable without retraining.
- A chronological train / tuning / calibration / test protocol, with targets purged at split boundaries.
- Seasonal mean and seasonal uncertainty baselines alongside ML policies.
- Paired Monte Carlo simulations: all policies face the same historical sales and supplier-delay draws.
- CSV recommendations and metrics; Parquet forecasts and simulation outcomes; configuration, data fingerprints, code fingerprints and model metadata.
- Tests for future-data leakage, physical stock conservation, capacity, pipeline accounting and model serialization; GitHub Actions runs tests without downloading M5.

`configs/local.json`: 64 deterministically sampled CA_1 series, 84-day final test, 20 delay simulations. `configs/kaggle.json`: 512 series, 100 simulations. Neither is a full M5 competition benchmark.

## Train on Kaggle

Open `notebooks/kaggle_training.ipynb`. Upload a source archive made with `python scripts/package_source.py` as a private Kaggle dataset, attach it to a notebook, and enable Internet for installing dependencies/downloading the mirror. CPU is sufficient; no paid GPU required. Alternatively attach official M5 evaluation sales and calendar files and set `DATA` in the notebook. The notebook copies source into `/kaggle/working`, trains the larger configuration, and bundles results for download. Read the data-source terms before using or redistributing data.

## The operational decision

Every seven days: estimate demand during **supplier lead time + time until the next review**, subtract stock on hand and outstanding orders, round to the case pack, and cap by available capacity. Comparing mean-based and uncertainty-aware policies exposes the cost of carrying safety stock versus losing sales.

The initial recommendation CSV uses hypothetical inventory. To use your own stock snapshot, follow `docs/OPERATIONS.md`. The project compares policies; it does not claim a globally optimal ordering solution. The approximate demand-distribution tails and lead-time distribution are explicit assumptions.

## Read before presenting

- [Measured results and interview insights (French)](docs/INSIGHTS_FR.md), with aggregate evidence in `docs/results`.
- [Methodology](docs/METHODOLOGY.md): temporal splits, quantile calibration, simulation assumptions and limitations.
- [Model card](docs/MODEL_CARD.md) and [data card](docs/DATA_CARD.md).
- [Operational walkthrough](docs/OPERATIONS.md): what a planner actually decides.
- Each completed run contains `SUMMARY.md` with measured results. Never substitute simulated savings for real operational savings.

## Repository layout

```text
src/inventory_intelligence/  data, features, training, evaluation, simulation, report
configs/                    small local and larger Kaggle experiments
notebooks/                  executable Kaggle workflow
scripts/                    download, inference and source packaging
tests/                      invariants and model persistence
docs/                       methodology, model/data cards, operational guide
data/                       ignored: original data and provenance manifest
runs/                       ignored: models, metrics and interactive reports
```

## Publish your own GitHub repository

Create an empty GitHub repository, then from this folder:

```sh
git init -b main
git add .
git diff --cached --stat
git commit -m "Build probabilistic demand and replenishment research pipeline"
git remote add origin <YOUR_REPOSITORY_URL>
git push -u origin main
```

Raw data, local environments and run artifacts are excluded. Review staged files before pushing. Code is MIT; third-party data is not relicensed by this repository.
