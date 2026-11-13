import numpy as np
import pandas as pd
from inventory_intelligence.model import Forecaster
from inventory_intelligence.data import boundaries

def test_small_end_to_end_and_artifact_reload(tmp_path):
    cfg={'seed':1,'test_days':28,'calibration_days':42,'tune_days':35,'history_days':200,'horizons':[7,9,12,16,21],'train_stride':14,'n_estimators':12,'learning_rate':.1,'num_leaves':7,'min_child_samples':10,'threads':1}
    rng=np.random.default_rng(2);y=rng.poisson(3,size=(4,400)).astype(float);d=pd.date_range('2020-01-01',periods=400).to_numpy()
    meta=pd.DataFrame({'id':list('abcd'),'dept_id':['D']*4,'cat_id':['C']*4,'store_id':['S']*4,'dept_id_code':[0]*4,'cat_id_code':[0]*4,'store_id_code':[0]*4})
    b=boundaries(400,cfg);model=Forecaster(cfg).fit(y,d,meta,b);pred=model.predict(y,d,meta,372,12)
    assert (pred['q10']<=pred['q50']).all();assert (pred['q50']<=pred['q90']).all();assert (pred['q10']>=0).all()
    model.save(tmp_path,meta);loaded=Forecaster.load(tmp_path);other=loaded.predict(y,d,meta,372,12)
    for k in pred:np.testing.assert_allclose(pred[k],other[k])
