import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pandas as pd
from .data import load_panel,boundaries
from .model import Forecaster
from .evaluation import evaluate
from .inventory import evaluate_inventory,policy_summary,targets_at
from .report import write_report

def validate(cfg):
    if cfg['review_days']<1 or cfg['case_pack']<1 or cfg['replications']<2:raise ValueError('Invalid review, pack or replication count')
    if not np.isclose(sum(cfg['lead_probabilities']),1) or any(x<0 for x in cfg['lead_probabilities']):raise ValueError('Lead probabilities must sum to 1')
    if len(cfg['lead_days'])!=len(cfg['lead_probabilities']) or min(cfg['lead_days'])<1:raise ValueError('Invalid lead distribution')
    if not all(x+cfg['review_days'] in cfg['horizons'] for x in cfg['lead_days']):raise ValueError('Train each protection horizon = lead + review')
    if not 0<cfg['risk_quantile']<1:raise ValueError('Invalid risk quantile')

def recommendations(model,y,dates,meta,cfg):
    target,samples=targets_at(model,y,dates,meta,y.shape[1],cfg)
    mean=y[:,-56:].mean(axis=1);onhand=np.ceil(mean*10);capacity=np.maximum(10,np.ceil(mean*cfg['capacity_days']))
    order=np.maximum(0,np.ceil((target['ml_risk']-onhand)/cfg['case_pack'])*cfg['case_pack']);order=np.minimum(order,np.maximum(0,np.floor((capacity-onhand)/cfg['case_pack'])*cfg['case_pack']))
    return pd.DataFrame({'series':meta.id,'hypothetical_onhand':onhand,'target_inventory_position':np.ceil(target['ml_risk']),'suggested_order':order,'capacity':capacity,'protection_exceedance_proxy':(samples>onhand[:,None]).mean(axis=1),'proxy_after_order':(samples>(onhand+order)[:,None]).mean(axis=1)}).sort_values('protection_exceedance_proxy',ascending=False)

def main():
    p=argparse.ArgumentParser(description='Train, evaluate and report probabilistic inventory policies')
    p.add_argument('--data',default='data/raw');p.add_argument('--config',default='configs/local.json');p.add_argument('--output',default=None)
    args=p.parse_args();cfg=json.loads(Path(args.config).read_text(encoding='utf-8'));validate(cfg)
    output=Path(args.output or ('runs/'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')))
    if output.exists():raise FileExistsError(f'Refusing to overwrite run: {output}')
    output.mkdir(parents=True);(output/'config.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    print('Loading real data...',flush=True);y,dates,meta=load_panel(args.data,cfg);b=boundaries(y.shape[1],cfg);meta.to_csv(output/'selected_series.csv',index=False)
    print('Fitting mean + three quantile LightGBM models...',flush=True);model=Forecaster(cfg).fit(y,dates,meta,b);model.save(output/'models',meta)
    print('Evaluating frozen model on rolling test origins...',flush=True);forecasts,metrics=evaluate(model,y,dates,meta,b,cfg)
    forecasts.to_parquet(output/'forecasts.parquet',index=False);metrics.to_csv(output/'forecast_metrics.csv',index=False)
    print('Comparing four inventory policies with paired lead-time simulations...',flush=True);rows,traces=evaluate_inventory(model,y,dates,meta,b,cfg);summary=policy_summary(rows)
    rows.to_parquet(output/'inventory_runs.parquet',index=False);traces.to_csv(output/'inventory_trace.csv',index=False);summary.to_csv(output/'policy_metrics.csv',index=False)
    reco=recommendations(model,y,dates,meta,cfg);reco.to_csv(output/'recommendations.csv',index=False)
    importance=pd.DataFrame({'feature':model.features,'mean_gain':model.models['mean'].feature_importance(importance_type='gain')}).sort_values('mean_gain',ascending=False);importance.to_csv(output/'feature_importance.csv',index=False)
    datafile=Path(args.data)/'sales_train_evaluation.csv'
    with datafile.open('rb') as handle:datahash=hashlib.file_digest(handle,'sha256').hexdigest()
    source_root=Path(__file__).parent
    manifest={'created_utc':datetime.now(timezone.utc).isoformat(),'n_series':len(y),'n_days':y.shape[1],'config':cfg,'splits':b,'split_dates':{k:str(pd.Timestamp(dates[min(v,len(dates)-1)]).date()) for k,v in b.items()},'data_sha256':datahash,'python':sys.version,'platform':platform.platform(),'packages':{x:importlib.metadata.version(x) for x in ['numpy','pandas','scikit-learn','lightgbm','scipy']},'code_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in source_root.glob('*.py')},'best_iterations':model.iterations,'interval_expansion_normalized':model.adjustments,'calibration_note':'Time dependence and overlapping windows violate exchangeability; empirical coverage is evaluated, no finite-sample deployment guarantee.'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');write_report(output,metrics,summary,rows,forecasts,traces,reco,manifest)
    print(summary.to_string(index=False));print('REPORT:',(output/'report.html').resolve(),flush=True)

if __name__=='__main__':main()
