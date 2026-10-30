"""Regenerate the founder memo from the supplied sample and current policy."""
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import mm
import pandas as pd
from engine import clean, config, evaluate, COST_RTO, MARGIN
from finance import financial_scenario

raw = pd.read_csv('orders_sample.csv')
df = clean(raw)
cfg = config()
scored = evaluate(df, cfg)
latest_month = pd.to_datetime(scored.order_datetime).dt.to_period('M').max()
month = scored[pd.to_datetime(scored.order_datetime).dt.to_period('M') == latest_month]
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='Small', parent=styles['BodyText'], fontSize=8.4, leading=11, spaceAfter=4))
story = []
def para(text, style='BodyText'):
    story.append(Paragraph(text, styles[style]))
    story.append(Spacer(1, 4))
def pct(n, d):
    return f'{(100*n/d):.2f}%' if d else 'n/a'
def segment(col, value):
    g = df[df[col].astype(str) == str(value)]
    n = len(g); r = int(g.status.eq('RTO').sum())
    return n, r, pct(r, n)

para('Founder memo | COD Decision Studio', 'Title')
para('To: Founder  |  Date: 30 October 2026  |  Based on supplied April–September 2026 sample', 'Small')
para('Recommendation', 'Heading2')
para(f"Pilot a staged policy: ship low-risk orders, confirm medium-risk COD orders, offer a modest prepaid incentive to higher-risk orders, and send the highest-risk or malformed records to human review. Do not automatically cancel based only on pincode or a risk score. The sample has {len(raw):,} rows; {len(df):,} resolved orders remain after normalising status labels and excluding unresolved records. {int(df.status.eq('RTO').sum()):,} resolved orders were RTO ({pct(int(df.status.eq('RTO').sum()),len(df))}). At ₹{COST_RTO:.2f} estimated cost per RTO, the sample's direct RTO logistics/handling/damage cost is ₹{int(df.status.eq('RTO').sum())*COST_RTO:,.2f}. This is historical sample cost, not a monthly forecast.")

para('What the data says', 'Heading2')
# Three data findings with explicit denominators.
n0, r0, p0 = segment('customer_prior_orders', 0)
n1, r1, p1 = segment('customer_prior_orders', 1)
n2, r2, p2 = segment('customer_prior_rto', 2)
meta_n, meta_r, meta_p = segment('utm_source', 'meta_ads')
direct_n, direct_r, direct_p = segment('utm_source', 'direct')
para(f"1. First-time orders are not automatically safe: {r0}/{n0} returned ({p0}) compared with {r1}/{n1} among customers with exactly one previous order ({p1}). A first order should get a trust-building confirmation path rather than a blanket block.", 'Small')
para(f"2. Repeat RTO history is a useful warning, but not certainty: {r2}/{n2} orders from customers with two previous RTOs returned ({p2}); {n2-r2} still delivered. That supports human review rather than automatic cancellation.", 'Small')
para(f"3. Acquisition source is a cohort signal, not proof of fraud: Meta Ads had {meta_r}/{meta_n} RTOs ({meta_p}); Direct had {direct_r}/{direct_n} ({direct_p}). Do not block an entire channel or pincode from these observational rates.", 'Small')

para('Recommended rules and historical replay', 'Heading2')
para(f"Use smoothed prior-RTO cohort rates with a 28% cold-start prior, small first-order/Meta adjustments, and deterministic name/pincode/address checks. Current configurable thresholds: ship below {cfg['ship_below']:.0%}; request WhatsApp confirmation from {cfg['ship_below']:.0%} to below {cfg['nudge_from']:.0%}; nudge prepaid from {cfg['nudge_from']:.0%} to below {cfg['hold_from']:.0%}; otherwise hold for human review. Invalid names or pincodes also go to review. The replay now scores each historical order using only resolved outcomes timestamped before that order; the current order and future outcomes are excluded from its risk estimate.", 'Small')
counts = scored.action.value_counts()
month_counts = month.action.value_counts()
table = [['Decision', f'All {len(scored):,}', f'{latest_month} ({len(month):,})']]
for action, label in [('Ship as-is','Ship as-is'),('Ship after confirmation','Confirm'),('Nudge to prepaid','Prepaid nudge'),('Hold / cancel','Hold / review')]:
    table.append([label, str(int(counts.get(action,0))), str(int(month_counts.get(action,0)))])
t = Table(table, colWidths=[72*mm, 35*mm, 43*mm], repeatRows=1)
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E8EDF4')),('GRID',(0,0),(-1,-1),0.35,colors.HexColor('#AAB4C2')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),('PADDING',(0,0),(-1,-1),5)]))
story.append(t); story.append(Spacer(1,6))

para('Operations versus Marketing: rupee trade-off', 'Heading2')
prepaid_saving = (0.28 - 0.04) * COST_RTO - cfg['prepaid_discount']
para(f"One RTO costs approximately ₹65 outbound + ₹65 return + ₹25 packaging/handling + (8% × ₹180) damaged inventory = ₹{COST_RTO:.2f}. A delivered ₹649 order contributes about ₹{649*MARGIN:.2f} at 62% gross margin. The stated 28% COD versus 4% prepaid RTO rates imply ₹{(0.28-0.04)*COST_RTO:.2f} expected RTO-cost reduction per converted prepaid order before discount. With the configured ₹{cfg['prepaid_discount']} discount, the direct RTO-cost-only difference is ₹{prepaid_saving:.2f}; this excludes payment fees and the additional contribution from a successfully delivered order. Conversion must be measured in a controlled pilot.", 'Small')
scen = financial_scenario(month, cfg)
para(f"For the latest sample month ({latest_month}), the dashboard's illustrative scenario estimates ₹{scen['rto_costs_avoided']:,.2f} RTO costs avoided, ₹{scen['incremental_delivered_contribution']:,.2f} incremental delivered contribution from assumed confirmations/prepaid conversions, ₹{scen['genuine_contribution_at_risk_if_held_orders_cancelled']:,.2f} genuine contribution at risk if every held order were cancelled, and ₹{scen['prepaid_discounts']:,.2f} discounts. The resulting scenario net is ₹{scen['net_incremental_value']:,.2f}. This is assumption-driven, not measured uplift: non-responders stay at baseline risk and are manually reviewed; held orders are assumed cancelled only to show downside.", 'Small')

para('Risks, monitoring and next two weeks', 'Heading2')
para('Monitor false-positive holds, RTO rate by action and cohort, confirmation response, prepaid conversion, contribution after discounts/payment fees, address-review overrides, pincode sample sizes, opt-outs, latency and drift. The sample has no observed WhatsApp responses or prepaid treatment outcomes, so the conversion and post-intervention RTO rates in the dashboard are explicit assumptions, not evidence. The LLM adapter is optional and unbenchmarked; it only advises on ambiguous address text and must not make dispatch/cancellation decisions. Do not send real customer personal data to an external model without approval and safeguards.', 'Small')
para('In the next two weeks: (1) run a small randomised confirmation/prepaid pilot with a holdout; (2) measure net contribution including gateway, messaging and staff costs; (3) evaluate Hinglish address review against a human-labelled test set; (4) add production WhatsApp templates, consent/opt-out handling, retries and verified payment webhooks; (5) monitor calibration and drift before increasing automation.', 'Small')

SimpleDocTemplate('Founder_Memo.pdf', pagesize=(210*mm,297*mm), leftMargin=15*mm, rightMargin=15*mm, topMargin=13*mm, bottomMargin=13*mm).build(story)
print(f'Wrote Founder_Memo.pdf from {len(df)} resolved rows; chronological replay buckets: {counts.to_dict()}')
