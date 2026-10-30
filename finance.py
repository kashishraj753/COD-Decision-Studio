"""Transparent scenario model; outputs are assumptions, not measured uplift."""
from engine import COST_RTO, MARGIN


def financial_scenario(day, cfg):
    """Estimate incremental value versus shipping every order as COD.

    Confirmation/prepaid effects apply only to the assumed share that responds
    or converts. Non-responders are assumed to remain at baseline risk (manual
    review after 24h). Held orders are modelled as cancelled for the conservative
    cancellation scenario; actual operating rule remains human review.
    """
    confirmed = day[day.action == 'Ship after confirmation']
    nudged = day[day.action == 'Nudge to prepaid']
    held = day[day.action == 'Hold / cancel']

    confirm_rate = float(cfg['assumed_confirmation_success'])
    confirm_delta = (confirmed.risk - float(cfg['assumed_rto_after_confirmation'])).clip(lower=0)
    confirm_avoided = float((confirm_delta * confirm_rate * COST_RTO).sum())
    confirm_extra_delivered = float((confirm_delta * confirm_rate * confirmed.order_value * MARGIN).sum())

    prepaid_rate = float(cfg['assumed_prepaid_conversion'])
    prepaid_delta = (nudged.risk - float(cfg['assumed_rto_after_prepaid'])).clip(lower=0)
    prepaid_avoided = float((prepaid_delta * prepaid_rate * COST_RTO).sum())
    prepaid_extra_delivered = float((prepaid_delta * prepaid_rate * nudged.order_value * MARGIN).sum())
    discounts = float(len(nudged) * prepaid_rate * float(cfg['prepaid_discount']))

    held_avoided = float((held.risk * COST_RTO).sum())
    held_contribution_at_risk = float(((1 - held.risk) * held.order_value * MARGIN).sum())
    avoided = confirm_avoided + prepaid_avoided + held_avoided
    incremental_contribution = confirm_extra_delivered + prepaid_extra_delivered
    net = avoided + incremental_contribution - held_contribution_at_risk - discounts
    return {
        'confirmation_rto_costs_avoided': confirm_avoided,
        'prepaid_rto_costs_avoided': prepaid_avoided,
        'held_rto_costs_avoided_if_cancelled': held_avoided,
        'rto_costs_avoided': avoided,
        'incremental_delivered_contribution': incremental_contribution,
        'genuine_contribution_at_risk_if_held_orders_cancelled': held_contribution_at_risk,
        'prepaid_discounts': discounts,
        'net_incremental_value': net,
        'assumptions': {
            'confirmation_success': confirm_rate,
            'prepaid_conversion': prepaid_rate,
            'rto_after_confirmation': float(cfg['assumed_rto_after_confirmation']),
            'rto_after_prepaid': float(cfg['assumed_rto_after_prepaid']),
            'nonresponders': 'baseline risk; sent to manual review after 24 hours',
            'held_orders': 'assumed cancelled for scenario only; actual policy is manual review',
            'excluded_costs': ['payment gateway fees', 'WhatsApp/message costs', 'staff review costs', 'tax effects'],
        }
    }
