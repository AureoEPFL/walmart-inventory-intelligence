"""Render figures from the committed experiment metrics. Requires matplotlib."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter,StrMethodFormatter
from datetime import datetime
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/assets';OUT.mkdir(exist_ok=True)
def rows(name):
 with (ROOT/'docs/results'/name).open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#314655','text.color':'#233d4c','axes.titleweight':'bold','figure.facecolor':'#f7f9fa','axes.facecolor':'#f7f9fa','savefig.facecolor':'#f7f9fa'})
policies={r['policy']:r for r in rows('policy_metrics.csv')}
keys=['seasonal_mean','seasonal_risk','ml_mean','ml_risk'];labels=['Seasonal\nmean','Seasonal +\nsafety stock','ML\nmean','ML +\nsafety stock'];colors=['#a9b6bf','#718d9d','#82a59d','#28675e']
fig,axes=plt.subplots(1,2,figsize=(12,4.9));fig.subplots_adjust(bottom=.22,top=.78,wspace=.34)
fig.suptitle('Walmart replenishment: cost and service must be judged together',fontsize=16,x=.07,ha='left',y=.96)
fig.text(.07,.87,'64 CA_1 products · 84-day holdout · 20 paired lead-time simulations',color='#647986')
cost=[float(policies[k]['mean_cost']) for k in keys];rate=[float(policies[k]['fill_rate']) for k in keys]
axes[0].bar(labels,cost,color=colors,width=.6,yerr=[[v-float(policies[k]['cost_mc95_low']) for v,k in zip(cost,keys)],[float(policies[k]['cost_mc95_high'])-v for v,k in zip(cost,keys)]],capsize=3)
axes[0].set_ylim(0,8600);axes[0].set_ylabel('Simulated inventory-related cost (USD)');axes[0].yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
for i,v in enumerate(cost):axes[0].text(i,v+230,f'${v:,.0f}',ha='center',weight='bold')
axes[1].bar(labels,rate,color=colors,width=.6);axes[1].set_ylim(0,1.08);axes[1].yaxis.set_major_formatter(PercentFormatter(1));axes[1].set_ylabel('Share of demand fulfilled (units)')
for i,v in enumerate(rate):axes[1].text(i,v+.025,f'{v:.2%}',ha='center',weight='bold')
fig.text(.07,.045,'Costs / stocks / lead times are assumed. Error bars: 95% Monte Carlo intervals conditional on fixed demand history.',fontsize=9,color='#647986')
fig.savefig(OUT/'cost-and-service.png',dpi=170);plt.close(fig)
metrics=rows('forecast_metrics.csv');fig,ax=plt.subplots(figsize=(10,4.8));fig.subplots_adjust(bottom=.2,top=.80)
for model,label,color in [('seasonal','Seasonal historical interval','#9b8875'),('lightgbm_calibrated','LightGBM calibrated interval','#28675e')]:
 data=sorted([r for r in metrics if r['model']==model],key=lambda r:int(r['horizon']))
 ax.plot([int(r['horizon']) for r in data],[float(r['coverage_80']) for r in data],marker='o',lw=2.5,label=label,color=color)
ax.axhline(.8,color='#647986',ls='--',lw=1,label='Nominal 80% coverage');ax.set_ylim(.5,1);ax.set_xticks([7,9,12,16,21]);ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_xlabel('Cumulative demand horizon (days)');ax.set_ylabel('Observed interval coverage');ax.legend(frameon=False,loc='lower left');ax.set_title('Does the uncertainty interval cover actual sales?',loc='left',pad=22)
fig.text(.12,.045,'Holdout coverage, not a guarantee for future demand. Wider intervals can increase safety stock.',fontsize=9,color='#647986');fig.savefig(OUT/'interval-coverage.png',dpi=170);plt.close(fig)
with (OUT/'forecast-example.csv').open(encoding='utf-8-sig') as f:data=list(csv.DictReader(f))
dates=[datetime.fromisoformat(r['origin_date']) for r in data]
fig,ax=plt.subplots(figsize=(10,4.8));fig.subplots_adjust(bottom=.24,top=.77)
ax.fill_between(dates,[float(r['q10']) for r in data],[float(r['q90']) for r in data],color='#d1e5de',label='10th–90th percentile interval')
ax.plot(dates,[float(r['q50']) for r in data],color='#28675e',lw=2,marker='o',label='Predicted median');ax.plot(dates,[float(r['actual']) for r in data],color='#a56d46',lw=2,marker='s',label='Observed cumulative sales')
fig.suptitle('Model output: 12-day demand, forecast versus observed',x=.12,ha='left',y=.96,fontsize=15,fontweight='bold');ax.set_ylabel('Units over the next 12 days');ax.set_xlabel('Forecast origin (weekly rolling evaluation)');ax.legend(frameon=False,loc='upper left',fontsize=9)
fig.text(.12,.84,data[0]['series']+' · alphabetically first sampled series; not selected for accuracy',fontsize=9,color='#647986');fig.text(.12,.045,'Overlapping forecast windows. Models remain frozen; past observed sales update the input features.',fontsize=9,color='#647986');fig.savefig(OUT/'forecast-example.png',dpi=170);plt.close(fig)
print('Rendered three result figures from saved metrics and forecasts.')
