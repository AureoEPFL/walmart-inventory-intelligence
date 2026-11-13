import numpy as np
import pandas as pd
import pytest
from inventory_intelligence.features import at_origin,supervised,seasonal_samples
from inventory_intelligence.inventory import simulate,policy_summary
from inventory_intelligence.data import boundaries

def fixture():
    y=np.random.default_rng(1).poisson(3,size=(3,250)).astype(float)
    dates=pd.date_range('2020-01-01',periods=250).to_numpy()
    meta=pd.DataFrame({'id':['a','b','c'],'dept_id_code':[0,0,1],'cat_id_code':[0,0,0],'store_id_code':[0,0,0]})
    return y,dates,meta

def test_future_mutation_cannot_change_features_or_baseline():
    y,d,m=fixture();before,scale=at_origin(y,d,m,100,16);base=seasonal_samples(y,100,16)
    y[:,100:]=1e9;after,newscale=at_origin(y,d,m,100,16)
    pd.testing.assert_frame_equal(before,after);np.testing.assert_equal(scale,newscale);np.testing.assert_equal(base,seasonal_samples(y,100,16))

def test_no_target_crosses_split_boundary():
    y,d,m=fixture();x,target,scale,k=supervised(y,d,m,60,140,[7,9,16,21])
    assert (k.label_end<=140).all()
    for j in [0,len(k)-1]:
        row=k.iloc[j];assert target[j]*scale[j]==pytest.approx(y[int(row.series),int(row.origin):int(row.label_end)].sum())

def test_series_boundaries_do_not_mix():
    y,d,m=fixture();y[0]=1;y[1]=100;y[2]=0;x,scale=at_origin(y,d,m,100,7)
    assert list(scale)==[2,101,1];assert x.zero_7.tolist()==[0,0,1]

def config():return {'review_days':2,'case_pack':1,'holding_cost':.1,'shortage_cost':5,'order_cost':1}

def test_pipeline_counted_no_double_order_and_mass_balance():
    cfg=config();d=np.zeros((1,6));targets={i:{'p':np.array([10.])} for i in [0,2,4]};lead=np.full((1,6),3)
    result,_=simulate(d,targets,lead,[0],[10],cfg,'p')
    assert result.orders.iloc[0]==1;assert result.ordered_units.iloc[0]==10;assert result.ending_onhand.iloc[0]==10

def test_lead_time_means_no_same_day_delivery():
    cfg=config();d=np.ones((1,4))*3;targets={i:{'p':np.array([20.])} for i in [0,2]};lead=np.full((1,4),2)
    result,_=simulate(d,targets,lead,[0],[20],cfg,'p')
    assert result.lost_units.iloc[0]==6;assert result.served_units.iloc[0]==6

def test_capacity_and_case_pack():
    cfg=config();cfg['case_pack']=6;d=np.zeros((1,4));targets={i:{'p':np.array([50.])} for i in [0,2]};lead=np.ones((1,4),dtype=int)
    result,_=simulate(d,targets,lead,[0],[10],cfg,'p');assert result.ordered_units.iloc[0]==6

def test_zero_demand_has_defined_service_rate():
    cfg=config();d=np.zeros((1,4));targets={i:{'p':np.array([0.])} for i in [0,2]};lead=np.ones((1,4),dtype=int)
    result,_=simulate(d,targets,lead,[0],[10],cfg,'p');assert result.fill_rate.iloc[0]==1;assert result.total_cost.iloc[0]==0

def test_forecast_origin_is_first_unobserved_day():
    y,d,m=fixture();y[:,99]=17;y[:,100]=900;x,scale=at_origin(y,d,m,100,7)
    np.testing.assert_allclose(x.lag_1*scale,17)
