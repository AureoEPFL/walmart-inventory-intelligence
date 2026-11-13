import numpy as np
import pandas as pd
from .features import seasonal_samples,at_origin

def evaluate(model,y,dates,meta,b,cfg):
    frames=[]
    for origin in range(b['test_start'],b['end'],7):
        for h in cfg['horizons']:
            if origin+h>b['end']:continue
            actual=y[:,origin:origin+h].sum(axis=1)
            x,scale=at_origin(y,dates,meta,origin,h)
            raw=model.predict_frame(x,scale,False);cal=model.predict_frame(x,scale,True)
            samples=seasonal_samples(y,origin,h)
            baseline={'mean':samples.mean(axis=1),**{f'q{int(q*100)}':np.quantile(samples,q,axis=1) for q in [.1,.5,.9]}}
            for name,p in [('seasonal',baseline),('lightgbm_raw',raw),('lightgbm_calibrated',cal)]:
                frames.append(pd.DataFrame({'model':name,'series':meta.id,'category':meta.cat_id,'origin':origin,'origin_date':str(pd.Timestamp(dates[origin]).date()),'horizon':h,'actual':actual,**p}))
    forecasts=pd.concat(frames,ignore_index=True)
    summary=[]
    for (name,h),f in forecasts.groupby(['model','horizon']):
        actual=f.actual.to_numpy();lo=f.q10.to_numpy();hi=f.q90.to_numpy();mean=f['mean'].to_numpy();med=f.q50.to_numpy()
        score=hi-lo+10*np.maximum(lo-actual,0)+10*np.maximum(actual-hi,0)
        row={'model':name,'horizon':int(h),'n':len(f),'mae':float(np.abs(actual-med).mean()),'rmse':float(np.sqrt(np.mean((actual-mean)**2))),'wape':float(np.abs(actual-mean).sum()/max(actual.sum(),1)),'bias':float((mean-actual).sum()/max(actual.sum(),1)),'coverage_80':float(((actual>=lo)&(actual<=hi)).mean()),'mean_interval_width':float((hi-lo).mean()),'interval_score_80':float(score.mean())}
        for q,col in [(.1,'q10'),(.5,'q50'),(.9,'q90')]:
            residual=actual-f[col].to_numpy();row[f'pinball_{int(q*100)}']=float(np.maximum(q*residual,(q-1)*residual).mean())
        summary.append(row)
    return forecasts,pd.DataFrame(summary)
