# Technical notes

The completed experiment uses `configs/local.json`: 64 CA_1 series and 20 delay simulations. `configs/kaggle.json` defines a larger, unexecuted configuration of 512 series and 100 simulations. Python 3.11+ is required; `requirements-lock.txt` records the initial environment.

The implementation entry points are:

```sh
python -m pip install -e ".[dev]"
python scripts/download_m5.py --commit 72b8e7fd3b565b3c538adcb1d1a05117d8562d7e
python -m inventory_intelligence.cli --config configs/local.json --output runs/experiment
python -m pytest -q
```

Each run writes its metrics, frozen models, configuration, provenance manifest and offline `report.html` to a new directory. Existing runs are never overwritten. `scripts/recommend.py` reloads saved models against an inventory snapshot. `notebooks/kaggle_training.ipynb` contains the larger-experiment workflow. Raw M5 data remains subject to its original terms and is not redistributed here.
