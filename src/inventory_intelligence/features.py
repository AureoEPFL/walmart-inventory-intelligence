import numpy as np
import pandas as pd

def at_origin(y,dates,meta,origin,horizon):
    """origin is first UNOBSERVED index. Every demand feature reads [:origin]."""
    if origin<56 or horizon<1:raise ValueError("Need 56 observed days and positive horizon")
    hist=y[:,max(0,origin-56):origin]
    scale=hist[:,-28:].mean(axis=1)+1.0
    x={"horizon":np.repeat(horizon,len(y)),"scale":scale}
    for w in [7,14,28,56]:
        a=hist[:,-w:]
        x[f"mean_{w}"]=a.mean(axis=1)/scale
        x[f"std_{w}"]=a.std(axis=1)/scale
        x[f"zero_{w}"]=(a==0).mean(axis=1)
    for lag in [1,7,14,28]:x[f"lag_{lag}"]=y[:,origin-lag]/scale
    x["trend"]=hist[:,-7:].mean(axis=1)/scale-hist[:,-28:].mean(axis=1)/scale
    target_date=pd.Timestamp(dates[origin]) if origin<len(dates) else pd.Timestamp(dates[-1])+pd.Timedelta(days=origin-len(dates)+1)
    x["dow"]=np.repeat(target_date.dayofweek,len(y));x["month"]=np.repeat(target_date.month,len(y))
    x["year_day_sin"]=np.repeat(np.sin(2*np.pi*target_date.dayofyear/365.25),len(y))
    x["year_day_cos"]=np.repeat(np.cos(2*np.pi*target_date.dayofyear/365.25),len(y))
    for col in ["dept_id_code","cat_id_code","store_id_code"]:x[col]=meta[col].to_numpy()
    return pd.DataFrame(x),scale

def supervised(y,dates,meta,start,label_end,horizons,stride=7):
    """Only include targets ending on or before label_end (strict split purge)."""
    blocks=[];targets=[];scales=[];keys=[]
    for origin in range(start,label_end,stride):
        for h in horizons:
            if origin+h>label_end:continue
            x,scale=at_origin(y,dates,meta,origin,h)
            blocks.append(x);targets.append(y[:,origin:origin+h].sum(axis=1)/scale);scales.append(scale)
            keys.append(pd.DataFrame({"series":np.arange(len(y)),"origin":origin,"horizon":h,"label_end":origin+h}))
    if not blocks:raise ValueError("Empty split")
    return pd.concat(blocks,ignore_index=True),np.concatenate(targets),np.concatenate(scales),pd.concat(keys,ignore_index=True)

def seasonal_samples(y,origin,horizon):
    """Same-weekday historical blocks, all observed by origin; preserves dependence."""
    samples=[]
    for weeks in range(1,17):
        start=origin-7*weeks
        if start<0:break
        if start+horizon<=origin:samples.append(y[:,start:start+horizon].sum(axis=1))
    if not samples:raise ValueError("Insufficient seasonal blocks")
    return np.stack(samples,axis=1)
