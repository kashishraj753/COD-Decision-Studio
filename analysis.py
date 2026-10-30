import pandas as pd
from engine import clean,config,evaluate,COST_RTO
x=clean(pd.read_csv('orders_sample.csv'));print('Completed',len(x),'Delivered',sum(x.status=='DELIVERED'),'RTO',sum(x.status=='RTO'),'RTO rate',round(x.status.eq('RTO').mean()*100,2),'Historical RTO cost',round(x.status.eq('RTO').sum()*COST_RTO,2))
for col in ['customer_prior_rto','customer_prior_orders','utm_source','courier']:
 print('\n',col);print(x.groupby(col).status.agg(n='size',rto=lambda s:s.eq('RTO').sum()).assign(rate=lambda a:(100*a.rto/a.n).round(2)).to_string())
y=evaluate(x,config());print('\nPolicy buckets (descriptive, in-sample):');print(pd.crosstab(y.action,y.status).to_string());print('\nMonthly buckets:');print(pd.crosstab(pd.to_datetime(y.order_datetime).dt.to_period('M'),y.action).to_string())
