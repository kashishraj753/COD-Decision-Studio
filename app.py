import json
import pandas as pd
import streamlit as st
from engine import clean,config,decide,evaluate,COST_RTO,MARGIN
from whatsapp import initial,reply,timeout,transition
from address_review import review
from finance import financial_scenario
from llm_review import interpret
st.set_page_config(page_title='COD Decision Engine',layout='wide')
st.markdown("""<style>
.block-container {padding-top:2rem; max-width:1250px}
[data-testid="stMetric"] {background:#172033;border:1px solid #34435d;border-radius:12px;padding:15px}
[data-testid="stMetricLabel"] {font-weight:650}
.stTabs [data-baseweb="tab"] {font-weight:650}
</style>""",unsafe_allow_html=True)
st.title('COD Decision Studio')
st.caption('Explainable COD triage · Historical evidence · Scenario modelling (not realised savings)')
df=clean(pd.read_csv('orders_sample.csv'));cfg=config()
with st.sidebar:
 st.header('Editable policy (no code changes)')
 st.info('Persist changes by editing config.json. These controls are session-only.')
 cfg['ship_below']=st.slider('Ship below',.05,.50,float(cfg['ship_below']),.01)
 cfg['nudge_from']=st.slider('Nudge from',cfg['ship_below'],.70,max(float(cfg['nudge_from']),cfg['ship_below']),.01)
 cfg['hold_from']=st.slider('Hold from',cfg['nudge_from'],.95,max(float(cfg['hold_from']),cfg['nudge_from']),.01)
 cfg['prepaid_discount']=st.number_input('Prepaid discount (Rs)',0,100,int(cfg['prepaid_discount']))
tab1,tab2,tab3,tab4,tab5=st.tabs(['Founder overview','New order','WhatsApp mock','Data insights','Policy lab'])
with tab1:
 df['date']=pd.to_datetime(df.order_datetime).dt.date
 selected=st.date_input('Business date (latest available date is preselected)',value=df.date.max(),min_value=df.date.min(),max_value=df.date.max())
 st.caption(f"Dataset coverage: {df.date.min()} to {df.date.max()}. No records exist for dates outside this range.")
 full=evaluate(df,cfg);day=full[full.date==selected]
 st.subheader('Orders by decision');st.bar_chart(day.action.value_counts().reindex(['Ship as-is','Ship after confirmation','Nudge to prepaid','Hold / cancel'],fill_value=0))
 a,b,c=st.columns(3)
 a.metric('Orders analysed',len(day));b.metric('Actual historical RTO',int(day.status.eq('RTO').sum()));c.metric('Historical RTO rate',f'{day.status.eq("RTO").mean():.1%}' if len(day) else 'N/A')
 st.caption('Scenario estimates only. The dataset has no WhatsApp responses or conversion experiment. Do not report these as achieved savings.')
 confirmed=day[day.action=='Ship after confirmation'];nudged=day[day.action=='Nudge to prepaid'];held=day[day.action=='Hold / cancel']
 # Transparent scenario model; assumptions are shown and editable in config.json.
 scenario=financial_scenario(day,cfg)
 a,b,c=st.columns(3)
 a.metric('Illustrative RTO costs avoided',f"₹{scenario['rto_costs_avoided']:,.2f}")
 b.metric('Genuine contribution at risk*',f"₹{scenario['genuine_contribution_at_risk_if_held_orders_cancelled']:,.2f}")
 c.metric('Illustrative net impact*',f"₹{scenario['net_incremental_value']:,.2f}")
 st.metric('Incremental delivered contribution (assumed conversions)',f"₹{scenario['incremental_delivered_contribution']:,.2f}")
 st.caption('Net = avoided RTO costs + incremental delivered contribution − contribution at risk from assumed cancellations − prepaid discounts. Non-responders remain at baseline risk and go to manual review.')
 st.caption(' *Scenario only, not realised savings or causal impact. Held orders are assumed cancelled solely to estimate the downside; actual policy is manual review. Excludes gateway, messaging and staff costs.')
 with st.expander('Financial assumptions used'):
  st.json(scenario['assumptions'])
 st.dataframe(day[['order_id','status','action','risk','reason']]);st.download_button('Download decision audit CSV',day.to_csv(index=False),'decisions.csv')
with tab2:
 with st.form('order'):
  name=st.text_input('Customer name','Anita Sharma');addr=st.text_input('Address','House 14, Station Road, near SBI Bank');pin=st.text_input('Pincode','110001');val=st.number_input('Order value',1,100000,649);prior=st.number_input('Prior orders',0,100,0);rto=st.number_input('Prior RTO',0,100,0);src=st.selectbox('Source',sorted(df.utm_source.unique()));submit=st.form_submit_button('Evaluate')
 if submit:
  st.session_state.pop('ai_review_result',None)
  st.session_state['evaluated_order']={'customer_name':name,'address':addr,'pincode':pin,'order_value':val,'customer_prior_orders':prior,'customer_prior_rto':rto,'utm_source':src}
 if 'evaluated_order' in st.session_state:
  order=st.session_state['evaluated_order']
  st.subheader('Address and identity review')
  st.json(review(order['customer_name'],order['address'],order['pincode']))
  result=decide(order,df,cfg);st.json(result)
  st.caption('Deterministic risk decision; optional AI review is advisory and never auto-cancels an order.')
  if st.button('Run optional live AI address interpretation (sends entered details to configured API)',key='ai_review'):
   st.session_state['ai_review_result']=interpret(order['customer_name'],order['address'],order['pincode'])
  if 'ai_review_result' in st.session_state:st.json(st.session_state['ai_review_result'])
with tab3:
 action=st.selectbox('Conversation flow',['Ship after confirmation','Nudge to prepaid']);lang=st.selectbox('Language',['hinglish','english']);amount=st.number_input('Order value (₹)',1,100000,649,key='wa_amount')
 signature=(action,lang,amount,cfg['prepaid_discount'])
 if st.session_state.get('wa_signature')!=signature:
  st.session_state['wa_signature']=signature;st.session_state['wa_reminded']=False;st.session_state['wa_state']='awaiting_reply';st.session_state['wa_history']=[('Business',initial(action,amount,cfg['prepaid_discount'],lang))]
 st.caption('Offline simulator — no actual WhatsApp messages, payment links or cancellations.')
 for sender,message in st.session_state['wa_history']:
  with st.chat_message('assistant' if sender=='Business' else 'user'):
   st.write(message)
 st.write('Mock status:',st.session_state['wa_state'].replace('_',' ').title())
 with st.form('wa_reply_form',clear_on_submit=True):
  msg=st.text_input('Customer reply (YES / NO / PAY / COD / question)')
  send=st.form_submit_button('Send reply')
 if send and msg.strip():
  state,response=transition(action,msg,st.session_state['wa_state'])
  st.session_state['wa_state']=state;st.session_state['wa_history'] += [('Customer',msg),('Business',response)];st.rerun()
 hours=st.slider('Hours since initial message',0,48,0)
 if st.button('Simulate elapsed time'):
  if st.session_state['wa_state'] in {'confirmed','cancel_requested','manual_review','prepaid_verified'}:
   note='Flow already closed; no further automatic action.'
  else:
   note=timeout(hours,cfg)
   if hours>=cfg['confirmation_hours']:st.session_state['wa_state']='manual_review'
   elif hours>=cfg['reminder_hours'] and not st.session_state.get('wa_reminded',False):st.session_state['wa_reminded']=True
   elif hours>=cfg['reminder_hours']:note='Reminder already sent; await response.'
  st.session_state['wa_history'].append(('Business',note));st.rerun()
 if st.button('Reset conversation'):
  st.session_state.pop('wa_signature',None);st.session_state.pop('wa_reminded',None);st.rerun()

with tab4:
 st.subheader('Observed historical patterns')
 st.caption('Descriptive analysis only; not proof of causation or out-of-sample model accuracy.')
 for column,title in [('customer_prior_rto','Previous RTO count'),('customer_prior_orders','Previous order count'),('utm_source','Acquisition channel')]:
  group=df.groupby(column).status.agg(orders='size',returns=lambda x:x.eq('RTO').sum()).reset_index()
  group['rto_rate']=group['returns']/group['orders']
  st.markdown(f'#### {title}')
  st.dataframe(group,hide_index=True,use_container_width=True)
  st.bar_chart(group.set_index(column)['rto_rate'])
 st.info('Historical order outcomes are real. WhatsApp and prepaid effects are assumptions; address-review accuracy has not been benchmarked.')

with tab5:
 st.subheader('What happens if we cancel more aggressively?')
 st.write('Compare two illustrative policies on the selected historical date. This is in-sample descriptive replay, not measured uplift.')
 rows=[]
 for label,hold in [('Current policy',cfg['hold_from']),('Aggressive hold test',max(cfg['nudge_from'],.30))]:
  policy={**cfg,'hold_from':hold}
  replay=evaluate(df,policy)
  replay=replay[replay.date==selected]
  held=replay[replay.action=='Hold / cancel']
  avoided=float((held.risk*COST_RTO).sum())
  at_risk=float(((1-held.risk)*held.order_value*MARGIN).sum())
  rows.append({'Policy':label,'Hold threshold':hold,'Held orders':len(held),'Avoided RTO cost if cancelled (₹)':round(avoided,2),'Genuine contribution at risk (₹)':round(at_risk,2),'Cancellation-only net (₹)':round(avoided-at_risk,2)})
 st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
 st.caption('The comparison isolates cancellation trade-offs; it excludes hypothetical confirmation/prepaid effects, payment fees and message costs. No order is actually cancelled.')
 st.markdown('**Why it matters:** a risky customer may still be genuine. Hold means manual verification, not automatic cancellation.')
