"""Explainable COD decision engine with leakage-safe chronological evaluation."""
import json
import re
import pandas as pd

FORWARD_SHIPPING = 65.0
RETURN_SHIPPING = 65.0
PACKAGING_HANDLING = 25.0
DAMAGE_RATE = 0.08
PRODUCT_COST = 180.0
COST_RTO = FORWARD_SHIPPING + RETURN_SHIPPING + PACKAGING_HANDLING + DAMAGE_RATE * PRODUCT_COST
MARGIN = 0.62
ACTIONS = ['Ship as-is', 'Ship after confirmation', 'Nudge to prepaid', 'Hold / cancel']


def config(path='config.json'):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def clean(df):
    df = df.copy()
    df['status'] = df['final_status'].astype(str).str.strip().str.upper()
    df = df[df.status.isin(['RTO', 'DELIVERED'])].copy()
    df['order_datetime'] = pd.to_datetime(df['order_datetime'], errors='coerce')
    df = df.dropna(subset=['order_datetime']).sort_values('order_datetime', kind='stable').reset_index(drop=True)
    for col in ['customer_prior_rto', 'customer_prior_orders', 'order_value']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['pincode'] = df['pincode'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    return df


def address_flags(o):
    address = str(o.get('address', '')).strip()
    name = str(o.get('customer_name', '')).strip().lower()
    pin = str(o.get('pincode', '')).strip().removesuffix('.0')
    fake_names = {'test', 'asdf', 'abc', 'xyz', 'na', 'none', 'qwerty', 'aaaa', 'dummy'}
    bad_name = name in fake_names or len(name) < 3 or bool(re.fullmatch(r'(.)\1{3,}', name))
    bad_pin = not bool(re.fullmatch(r'[1-9][0-9]{5}', pin))
    weak_address = len(address) < 15 or len(address.split()) < 3
    return bad_name, bad_pin, weak_address


def risk(o, history, cfg=None):
    """Estimate risk using only outcomes available before this order.

    Cold-start prior is the assignment's approximate 28% COD RTO rate. The
    empirical cohort is smoothed toward that prior; no target/future outcomes
    are included when called by evaluate().
    """
    cfg = cfg or {}
    base = float(cfg.get('cold_start_risk', 0.28))
    hist = history if history is not None else pd.DataFrame()
    if len(hist) and 'status' in hist:
        base = float(hist.status.eq('RTO').mean())
        r = int(float(o.get('customer_prior_rto', 0) or 0))
        cohort = hist[pd.to_numeric(hist.customer_prior_rto, errors='coerce').fillna(-1).astype(int).eq(r)]
        p = (int(cohort.status.eq('RTO').sum()) + 30 * base) / (len(cohort) + 30)
        sample_n = len(cohort)
    else:
        p = base
        sample_n = 0
    n = int(float(o.get('customer_prior_orders', 0) or 0))
    source = str(o.get('utm_source', '')).strip().lower()
    if n == 0:
        p += 0.025
    if source == 'meta_ads':
        p += 0.02
    bad_name, bad_pin, weak_address = address_flags(o)
    p += 0.12 * bad_name + 0.12 * bad_pin + 0.04 * weak_address
    return min(0.95, max(0.02, p)), sample_n


def decide(o, history, cfg):
    p, cohort_n = risk(o, history, cfg)
    bad_name, bad_pin, weak = address_flags(o)
    if bad_name or bad_pin:
        action = 'Hold / cancel'
        why = 'Name or pincode needs manual verification; do not automatically cancel.'
    elif p < cfg['ship_below']:
        action = 'Ship as-is'
        why = 'Estimated return risk is below the shipping threshold.'
    elif p < cfg['nudge_from']:
        action = 'Ship after confirmation'
        why = 'Confirm the COD order on WhatsApp before dispatch.'
    elif p < cfg['hold_from']:
        action = 'Nudge to prepaid'
        why = 'Offer prepaid conversion to reduce expected return risk.'
    else:
        action = 'Hold / cancel'
        why = 'High estimated risk; hold for human review, not automatic cancellation.'
    if weak and not (bad_name or bad_pin):
        why += ' Address details may need a landmark or house number.'
    return {
        'action': action,
        'risk': round(float(p), 4),
        'reason': why,
        'historical_cohort_n': int(cohort_n),
        'expected_rto_loss_if_shipped': round(float(p) * COST_RTO, 2),
        'expected_delivered_contribution': round((1 - float(p)) * float(o.get('order_value', 0)) * MARGIN, 2),
    }


def evaluate(df, cfg):
    """Chronological replay: score each order from strictly earlier resolved orders."""
    data = clean(df) if 'status' not in df.columns else df.sort_values('order_datetime', kind='stable').reset_index(drop=True).copy()
    results = []
    history_rows = []
    for _, row in data.iterrows():
        outcome = decide(row.to_dict(), pd.DataFrame(history_rows), cfg)
        results.append(outcome)
        history_rows.append(row.to_dict())
    scored = pd.DataFrame(results)
    return pd.concat([data.reset_index(drop=True), scored.reset_index(drop=True)], axis=1)
