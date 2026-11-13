import html
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def write_report(path,metrics,policies,rows,forecasts,traces,recommendations,manifest):
    path=Path(path)
    palette=['#314d5c','#96aaa1','#bc9474','#6d7f99']
    figs=[]
    fig=px.bar(policies,x='policy',y='mean_cost',color='policy',color_discrete_sequence=palette,title='Inventory cost — same demand and paired random lead times')
    fig.update_traces(showlegend=False);fig.update_layout(yaxis_title='Simulated cost ($), full test portfolio');figs.append(fig)
    fig=px.scatter(policies,x='mean_cost',y='fill_rate',text='policy',color='policy',color_discrete_sequence=palette,title='Service / cost trade-off');fig.update_traces(textposition='top center');fig.update_layout(yaxis_tickformat='.1%');figs.append(fig)
    fig=px.line(metrics,x='horizon',y='coverage_80',color='model',markers=True,title='Empirical coverage of nominal 80% cumulative-demand intervals');fig.add_hline(y=.8,line_dash='dash');fig.update_layout(yaxis_tickformat='.0%');figs.append(fig)
    fig=px.line(metrics,x='horizon',y='wape',color='model',markers=True,title='Demand-weighted forecast error (mean predictions)');fig.update_layout(yaxis_tickformat='.1%');figs.append(fig)
    fig=px.line(traces,x='day',y='onhand',color='policy',title='Inventory trajectory — lead-time replication 0');figs.append(fig)
    f=forecasts[(forecasts.model=='lightgbm_calibrated')&(forecasts.horizon==12)]
    ids=sorted(f.series.unique());fig=go.Figure()
    for i,sku in enumerate(ids):
        g=f[f.series==sku].sort_values('origin')
        for name,col,color,fill in [('Upper 90%','q90','#adc3b7',None),('Lower 10%','q10','#adc3b7','tonexty'),('Median','q50','#36544e',None),('Actual','actual','#b47643',None)]:
            fig.add_trace(go.Scatter(x=g.origin_date,y=g[col],name=name,mode='lines+markers',line={'color':color},fill=fill,visible=i==0))
    fig.update_layout(title='12-day cumulative sales: inspect any sampled SKU',updatemenus=[{'buttons':[{'label':sku,'method':'update','args':[{'visible':[j//4==i for j in range(4*len(ids))]}]} for i,sku in enumerate(ids)],'x':0,'y':1.18}]);figs.append(fig)
    blocks=[]
    for i,fig in enumerate(figs):
        fig.update_layout(template='plotly_white',font={'family':'Arial','color':'#263b43'},margin={'l':55,'r':30,'t':90,'b':60},height=420)
        blocks.append(fig.to_html(full_html=False,include_plotlyjs=True if i==0 else False))
    best=policies.loc[policies.mean_cost.idxmin()]
    comparisons=paired_comparisons(rows);comparisons.to_csv(path/'paired_comparisons.csv',index=False)
    sensitivity=[]
    for penalty in [2,5,10,20]:
        for policy,g in rows.groupby('policy'):
            costs=(g.holding_cost+g.ordering_cost+penalty*g.lost_units).groupby(g.replication).sum()
            sensitivity.append({'shortage_cost_per_unit':penalty,'policy':policy,'mean_cost':costs.mean()})
    sens=pd.DataFrame(sensitivity);sens.to_csv(path/'cost_sensitivity.csv',index=False)
    fig=px.line(sens,x='shortage_cost_per_unit',y='mean_cost',color='policy',markers=True,title='Cost sensitivity — fixed policies, changed shortage penalty');fig.update_layout(template='plotly_white');blocks.append(fig.to_html(full_html=False,include_plotlyjs=False))
    summary=f"""# Measured run: {path.name}

- Real M5 retail sales: {manifest['n_series']} sampled series, store {manifest['config']['store']}.
- Training/tuning/calibration/test are chronological and target-purged.
- Lowest simulated mean cost in this run: **{best['policy']}**, ${best['mean_cost']:,.2f}; unit fill rate {best['fill_rate']:.2%}.
- This is a retrospective comparison, not an independently validated policy selection. No claim that ML necessarily beats the seasonal baseline.
- Costs, starting stocks, capacity and lead times are assumptions. M5 has sales, not observed inventory or unmet demand.
- Monte Carlo intervals condition on this fixed demand history. They do not quantify all model/data uncertainty.

## Policy results

{policies.to_csv(index=False)}
## Paired differences versus seasonal_mean

{comparisons.to_csv(index=False)}
## Interview angles

1. Compare seasonal_risk and ml_risk at similar service levels, not just mean forecast error.
2. Inspect interval coverage by horizon; calibration is measured, not presumed.
3. Use cost_sensitivity.csv to explain how the preferred policy changes with shortage cost.
4. Explain why all four policies see the same demand and lead-time random numbers.
5. The recommendation snapshot uses hypothetical starting stock, not Walmart's actual inventory.
"""
    (path/'SUMMARY.md').write_text(summary,encoding='utf-8')
    body=f"""<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Inventory Intelligence — Evidence report</title><style>body{{font:15px Arial;background:#f5f5f0;color:#263b43;margin:0}}main{{max-width:1150px;margin:auto;padding:45px 25px}}h1{{font-size:42px;font-weight:500}}p{{line-height:1.7}}.card{{background:white;padding:24px;border:1px solid #dde1dd;border-radius:10px;margin:20px 0}}.tag{{font-size:11px;letter-spacing:2px}}table{{border-collapse:collapse;font-size:11px;width:100%}}td,th{{padding:9px;border-bottom:1px solid #ddd;text-align:left}}.scroll{{overflow:auto}}details{{margin:20px 0}}</style><main><div class='tag'>DEMAND → UNCERTAINTY → INVENTORY DECISION</div><h1>When should we order?</h1><p>A reproducible experiment on {manifest['n_series']} real M5 retail sales series. Forecast cumulative demand, simulate variable supplier lead times, compare cost and service.</p><div class='card'><b>What this run actually shows</b><p>Lowest simulated mean cost: <b>{best['policy']}</b> — ${best['mean_cost']:,.0f}, with {best['fill_rate']:.1%} unit fill rate. This result is conditional on the assumptions and this historical window.</p><p>Professional research prototype. Not production validated. Observed sales are used as a demand proxy; historical stockout censoring cannot be recovered.</p></div>{''.join('<section class="card">'+block+'</section>' for block in blocks)}<section class='card'><h2>Replenishment snapshot</h2><p>Hypothetical on-hand stock = 10 days of trailing sales, no open orders. Protection-period exceedance is a model proxy, not a calibrated probability of an operational stockout.</p><div class='scroll'>{recommendations.head(30).to_html(index=False,float_format=lambda x:f'{x:.3f}',escape=True)}</div></section><details><summary>Experiment manifest and assumptions</summary><pre>{html.escape(__import__('json').dumps(manifest,indent=2))}</pre></details></main></html>"""
    (path/'report.html').write_text(body,encoding='utf-8')

def paired_comparisons(rows):
    totals=rows.groupby(['replication','policy']).total_cost.sum().unstack()
    records=[]
    for policy in totals:
        delta=(totals[policy]-totals['seasonal_mean']).to_numpy();se=np.std(delta,ddof=1)/np.sqrt(len(delta)) if len(delta)>1 else 0
        records.append({'policy':policy,'mean_cost_difference':float(delta.mean()),'paired_mc95_low':float(delta.mean()-1.96*se),'paired_mc95_high':float(delta.mean()+1.96*se)})
    return pd.DataFrame(records)
