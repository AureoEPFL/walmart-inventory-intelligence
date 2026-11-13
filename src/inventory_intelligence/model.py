import json
from pathlib import Path
import lightgbm as lgb
import numpy as np
from .features import supervised,at_origin

QUANTILES=[.1,.5,.9]

class Forecaster:
    def __init__(self,cfg):self.cfg=cfg;self.models={};self.adjustments={};self.features=[];self.iterations={}

    def fit(self,y,dates,meta,b):
        cfg=self.cfg
        tx,ty,_,_=supervised(y,dates,meta,b['train_start'],b['tune_start'],cfg['horizons'],cfg['train_stride'])
        vx,vy,_,_=supervised(y,dates,meta,b['tune_start'],b['cal_start'],cfg['horizons'],7)
        fx,fy,_,_=supervised(y,dates,meta,b['train_start'],b['cal_start'],cfg['horizons'],cfg['train_stride'])
        self.features=list(tx.columns)
        for name in ['mean','q10','q50','q90']:
            params=dict(n_estimators=cfg['n_estimators'],learning_rate=cfg['learning_rate'],num_leaves=cfg['num_leaves'],min_child_samples=cfg['min_child_samples'],n_jobs=cfg['threads'],random_state=cfg['seed'],verbosity=-1,deterministic=True,force_col_wise=True,reg_lambda=1.0)
            if name=='mean':params.update(objective='tweedie',tweedie_variance_power=1.3)
            else:params.update(objective='quantile',alpha=int(name[1:])/100)
            selector=lgb.LGBMRegressor(**params)
            selector.fit(tx,ty,eval_set=[(vx,vy)],callbacks=[lgb.early_stopping(35,verbose=False)])
            self.iterations[name]=max(1,selector.best_iteration_)
            params['n_estimators']=self.iterations[name]
            estimator=lgb.LGBMRegressor(**params).fit(fx,fy)
            self.models[name]=estimator.booster_
        cx,cy,scale,keys=supervised(y,dates,meta,b['cal_start'],b['test_start'],cfg['horizons'],7)
        raw=self.predict_frame(cx,scale,calibrated=False)
        actual=cy*scale
        for h in cfg['horizons']:
            mask=keys.horizon.to_numpy()==h
            scores=np.maximum((raw['q10'][mask]-actual[mask])/scale[mask],(actual[mask]-raw['q90'][mask])/scale[mask])
            level=min(1,np.ceil((len(scores)+1)*.8)/len(scores))
            self.adjustments[str(h)]=float(max(0,np.quantile(scores,level,method='higher')))
        return self

    def predict_frame(self,x,scale,calibrated=True):
        pred={k:np.maximum(0,m.predict(x[self.features],num_threads=self.cfg['threads']))*scale for k,m in self.models.items()}
        ordered=np.sort(np.stack([pred['q10'],pred['q50'],pred['q90']],axis=1),axis=1)
        pred.update(q10=ordered[:,0],q50=ordered[:,1],q90=ordered[:,2])
        if calibrated and self.adjustments:
            delta=np.array([self.adjustments[str(int(h))] for h in x.horizon])*scale
            pred['q10']=np.maximum(0,pred['q10']-delta);pred['q90']+=delta
        return pred

    def predict(self,y,dates,meta,origin,horizon):
        if horizon not in self.cfg['horizons']:raise ValueError('Horizon was not trained')
        x,scale=at_origin(y,dates,meta,origin,horizon)
        return self.predict_frame(x,scale)

    def save(self,path,meta):
        path=Path(path);path.mkdir(parents=True,exist_ok=True)
        for k,m in self.models.items():(path/f'{k}.txt').write_text(m.model_to_string(),encoding='utf-8')
        (path/'schema.json').write_text(json.dumps({'config':self.cfg,'features':self.features,'adjustments':self.adjustments,'iterations':self.iterations,'categories':{c:sorted(meta[c].unique().tolist()) for c in ['dept_id','cat_id','store_id']}},indent=2),encoding='utf-8')

    @classmethod
    def load(cls,path):
        path=Path(path);schema=json.loads((path/'schema.json').read_text(encoding='utf-8'));obj=cls(schema['config']);obj.features=schema['features'];obj.adjustments=schema['adjustments'];obj.iterations=schema['iterations'];obj.models={k:lgb.Booster(model_str=(path/f'{k}.txt').read_text(encoding='utf-8')) for k in ['mean','q10','q50','q90']};return obj
