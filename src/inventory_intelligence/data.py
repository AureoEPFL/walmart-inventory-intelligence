import hashlib
from pathlib import Path
import numpy as np
import pandas as pd

def load_panel(root,config):
    """Deterministic metadata-only sampling. No target-based winner selection."""
    root=Path(root)
    path=root/"sales_train_evaluation.csv"
    if not path.exists():raise FileNotFoundError(f"Missing {path}. Run scripts/download_m5.py or attach Kaggle M5 data.")
    parts=[]
    for chunk in pd.read_csv(path,chunksize=1000):
        selected=chunk if config["store"]=="all" else chunk[chunk.store_id==config["store"]]
        if len(selected):parts.append(selected)
    if not parts:raise ValueError("No series for the requested store")
    frame=pd.concat(parts,ignore_index=True)
    # Nixtla's mirror omits Kaggle's redundant id column.
    if 'id' not in frame:frame['id']=frame.item_id.astype(str)+'_'+frame.store_id.astype(str)
    frame["selection_hash"]=frame.id.map(lambda x:hashlib.sha256(f'{config["seed"]}:{x}'.encode()).hexdigest())
    frame=frame.sort_values("selection_hash").head(config["n_series"]).reset_index(drop=True)
    cols=sorted([x for x in frame if x.startswith("d_")],key=lambda x:int(x[2:]))
    if cols!=[f"d_{i}" for i in range(1,len(cols)+1)]:raise ValueError("Sales days must be continuous")
    y=frame[cols].to_numpy(dtype=np.float32)
    if not np.isfinite(y).all() or (y<0).any():raise ValueError("Sales must be finite and nonnegative")
    if frame.id.duplicated().any():raise ValueError("Duplicate series")
    calendar=pd.read_csv(root/"calendar.csv")
    if 'd' not in calendar:
        parsed=pd.to_datetime(calendar['date'])
        calendar['d']='d_'+((parsed-pd.Timestamp('2011-01-29')).dt.days+1).astype(str)
    dates=pd.to_datetime(calendar.set_index("d").loc[cols,"date"]).to_numpy()
    meta=frame[["id","item_id","dept_id","cat_id","store_id","state_id"]].copy()
    for col in ["dept_id","cat_id","store_id"]:meta[col+"_code"]=pd.Categorical(meta[col],categories=sorted(meta[col].unique())).codes
    return y,dates,meta

def boundaries(length,cfg):
    test_start=length-cfg["test_days"]
    cal_start=test_start-cfg["calibration_days"]
    tune_start=cal_start-cfg["tune_days"]
    train_start=max(56,tune_start-cfg["history_days"])
    if tune_start-train_start<100:raise ValueError("Insufficient training history")
    return {"train_start":train_start,"tune_start":tune_start,"cal_start":cal_start,"test_start":test_start,"end":length}
