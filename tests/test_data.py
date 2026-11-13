import pandas as pd
import numpy as np
from inventory_intelligence.data import load_panel

def test_mirror_and_official_calendar_schema_match(tmp_path):
    frame=pd.DataFrame({'item_id':['FOODS_1_001'],'dept_id':['FOODS_1'],'cat_id':['FOODS'],'store_id':['CA_1'],'state_id':['CA']})
    for i in range(1,4):frame[f'd_{i}']=i
    frame.to_csv(tmp_path/'sales_train_evaluation.csv',index=False)
    calendar=pd.DataFrame({'date':pd.date_range('2011-01-29',periods=3)})
    calendar.to_csv(tmp_path/'calendar.csv',index=False)
    cfg={'store':'CA_1','seed':42,'n_series':1}
    a,dates,meta=load_panel(tmp_path,cfg)
    calendar['d']=['d_1','d_2','d_3'];calendar.to_csv(tmp_path/'calendar.csv',index=False)
    b,other,_=load_panel(tmp_path,cfg)
    np.testing.assert_equal(a,b);np.testing.assert_equal(dates,other)
    assert meta.id.tolist()==['FOODS_1_001_CA_1']
