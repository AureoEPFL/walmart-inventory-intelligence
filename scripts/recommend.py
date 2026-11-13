"""Reload frozen models and recommend quantities against a supplied stock CSV."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pandas as pd
from inventory_intelligence.data import load_panel
from inventory_intelligence.model import Forecaster
from inventory_intelligence.inventory import targets_at

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--data',default='data/raw');p.add_argument('--stock',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    if Path(a.output).exists():raise FileExistsError('Output already exists')
    model=Forecaster.load(Path(a.run)/'models');cfg=model.cfg
    y,dates,meta=load_panel(a.data,cfg)
    expected=pd.read_csv(Path(a.run)/'selected_series.csv').id.tolist()
    if meta.id.tolist()!=expected:raise ValueError('Series differ from training run')
    stock=pd.read_csv(a.stock).set_index('series')
    if stock.index.duplicated().any() or set(stock.index)!=set(expected):raise ValueError('Stock must contain exactly the trained series')
    stock=stock.loc[expected,['onhand','pipeline','capacity']]
    if not np.isfinite(stock.to_numpy()).all() or (stock<0).any().any():raise ValueError('Stock values must be finite and nonnegative')
    position=stock.onhand+stock.pipeline
    if (position>stock.capacity).any():raise ValueError('Stock and pipeline exceed reserved capacity')
    targets,_=targets_at(model,y,dates,meta,y.shape[1],cfg);pack=cfg['case_pack']
    stock['target']=targets['ml_risk'];stock['suggested_order']=np.minimum(np.maximum(0,np.ceil((stock.target-position)/pack)*pack),np.floor((stock.capacity-position)/pack)*pack)
    stock.to_csv(a.output);print('Recommendations:',Path(a.output).resolve())

if __name__=='__main__':main()
