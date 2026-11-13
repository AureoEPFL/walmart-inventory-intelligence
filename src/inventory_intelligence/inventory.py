import numpy as np
import pandas as pd
from .features import seasonal_samples

POLICIES=['seasonal_mean','seasonal_risk','ml_mean','ml_risk']

def targets_at(model,y,dates,meta,origin,cfg):
    """Lead-time mixture of cumulative demand, not sums of daily quantiles.

    ML mixture uses a documented piecewise-linear quantile approximation with
    capped extrapolated tails. This is an assumption, not a calibrated CDF.
    """
    leads=np.array(cfg['lead_days']);weights=np.array(cfg['lead_probabilities'])
    rng=np.random.default_rng(cfg['seed']+origin)
    choices=rng.choice(len(leads),size=3000,p=weights);u=rng.uniform(size=3000)
    ml_samples=np.zeros((len(y),len(choices)));base_samples=ml_samples.copy()
    ml_mean=np.zeros(len(y));base_mean=ml_mean.copy()
    for k,lead in enumerate(leads):
        h=int(lead)+cfg['review_days'];pred=model.predict(y,dates,meta,origin,h);hist=seasonal_samples(y,origin,h)
        ml_mean+=weights[k]*pred['mean'];base_mean+=weights[k]*hist.mean(axis=1)
        mask=choices==k
        for i in range(len(y)):
            tail=pred['q90'][i]+max(pred['q90'][i]-pred['q50'][i],1)
            ml_samples[i,mask]=np.interp(u[mask],[0,.1,.5,.9,1],[0,pred['q10'][i],pred['q50'][i],pred['q90'][i],tail])
            base_samples[i,mask]=np.quantile(hist[i],u[mask])
    targets={'seasonal_mean':base_mean,'seasonal_risk':np.quantile(base_samples,cfg['risk_quantile'],axis=1),'ml_mean':ml_mean,'ml_risk':np.quantile(ml_samples,cfg['risk_quantile'],axis=1)}
    return targets,ml_samples

def simulate(demand,targets,lead_schedule,initial,capacity,cfg,policy):
    """Daily lost-sales system, receipts -> weekly review/order -> demand.

    Capacity reserves both on-hand and in-transit stock. No demand is backlogged.
    """
    n_series,n_days=demand.shape;onhand=np.array(initial,dtype=float).copy();capacity=np.asarray(capacity,dtype=float);pipeline=[]
    holding=np.zeros(n_series);lost=np.zeros(n_series);served=np.zeros(n_series);orders=np.zeros(n_series);received=np.zeros(n_series);ordered=np.zeros(n_series);stockout=np.zeros(n_series)
    trace=[]
    for day in range(n_days):
        remaining=[]
        for due,qty in pipeline:
            arrive=due==day;onhand+=qty*arrive;received+=qty*arrive
            if (~arrive).any():remaining.append((due,np.where(arrive,0,qty)))
        pipeline=remaining
        in_transit=sum((qty for _,qty in pipeline),start=np.zeros(n_series))
        if day%cfg['review_days']==0:
            desired=np.maximum(0,targets[day][policy]-onhand-in_transit)
            pack=cfg['case_pack'];qty=np.ceil(desired/pack)*pack
            free=np.maximum(0,capacity-onhand-in_transit)
            qty=np.minimum(qty,np.floor(free/pack)*pack)
            orders+=(qty>0);ordered+=qty;pipeline.append((day+lead_schedule[:,day],qty));in_transit+=qty
        current=np.minimum(onhand,demand[:,day]);short=demand[:,day]-current;served+=current;lost+=short;stockout+=(short>0);onhand-=current;holding+=onhand
        if day%7==0:trace.append({'day':day,'onhand':float(onhand.sum()),'pipeline':float(in_transit.sum()),'lost_today':float(short.sum())})
        if (onhand<-.0001).any() or (onhand+in_transit>capacity+.0001).any():raise AssertionError('Physical inventory constraint violated')
    ending_pipeline=sum((qty for _,qty in pipeline),start=np.zeros(n_series))
    if not np.allclose(np.array(initial)+received-served,onhand):raise AssertionError('Mass balance violated')
    frame=pd.DataFrame({'holding_unit_days':holding,'lost_units':lost,'served_units':served,'orders':orders,'stockout_days':stockout,'ending_onhand':onhand,'ending_pipeline':ending_pipeline,'ordered_units':ordered})
    frame['holding_cost']=holding*cfg['holding_cost'];frame['shortage_cost']=lost*cfg['shortage_cost'];frame['ordering_cost']=orders*cfg['order_cost'];frame['total_cost']=frame.holding_cost+frame.shortage_cost+frame.ordering_cost
    frame['fill_rate']=np.divide(served,served+lost,out=np.ones_like(served),where=(served+lost)>0)
    return frame,trace

def evaluate_inventory(model,y,dates,meta,b,cfg):
    start=b['test_start'];demand=y[:,start:b['end']];ndays=demand.shape[1]
    frozen_daily=y[:,start-56:start].mean(axis=1)
    capacity=np.maximum(10,np.ceil(cfg['capacity_days']*frozen_daily))
    initial=np.minimum(capacity,np.ceil(cfg['initial_cover_days']*frozen_daily))
    cache={}
    for day in range(0,ndays,cfg['review_days']):cache[day]=targets_at(model,y,dates,meta,start+day,cfg)[0]
    rows=[];traces=[]
    for rep in range(cfg['replications']):
        # Same random lead by series AND calendar day for every policy.
        rng=np.random.default_rng(cfg['seed']+10000+rep)
        lead=rng.choice(cfg['lead_days'],size=(len(y),ndays),p=cfg['lead_probabilities'])
        for policy in POLICIES:
            frame,trace=simulate(demand,cache,lead,initial,capacity,cfg,policy)
            frame['policy']=policy;frame['replication']=rep;frame['series']=meta.id.to_numpy();frame['category']=meta.cat_id.to_numpy();rows.append(frame)
            if rep==0:traces.extend([{**r,'policy':policy} for r in trace])
    return pd.concat(rows,ignore_index=True),pd.DataFrame(traces)

def policy_summary(rows):
    records=[]
    for policy,f in rows.groupby('policy'):
        rep=f.groupby('replication').sum(numeric_only=True);cost=rep.total_cost.to_numpy();se=cost.std(ddof=1)/np.sqrt(len(cost)) if len(cost)>1 else 0
        records.append({'policy':policy,'mean_cost':float(cost.mean()),'cost_mc95_low':float(cost.mean()-1.96*se),'cost_mc95_high':float(cost.mean()+1.96*se),'fill_rate':float(rep.served_units.sum()/max(1,rep.served_units.sum()+rep.lost_units.sum())),'lost_units':float(rep.lost_units.mean()),'holding_cost':float(rep.holding_cost.mean()),'ordering_cost':float(rep.ordering_cost.mean()),'ending_onhand':float(rep.ending_onhand.mean()),'ending_pipeline':float(rep.ending_pipeline.mean())})
    return pd.DataFrame(records)
