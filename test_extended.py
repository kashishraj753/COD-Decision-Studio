import unittest
import pandas as pd
from whatsapp import transition, timeout
from engine import COST_RTO, MARGIN, clean, decide, config, evaluate
from address_review import review
from finance import financial_scenario

class Extended(unittest.TestCase):
    def setUp(self):
        self.raw = pd.read_csv('orders_sample.csv')
        self.df = clean(self.raw)
        self.cfg = config()

    def test_financial_constants(self):
        self.assertAlmostEqual(COST_RTO, 169.4)
        self.assertAlmostEqual(MARGIN, .62)

    def test_confirmation_flow(self):
        self.assertEqual(transition('Ship after confirmation', 'YES')[0], 'confirmed')
        self.assertEqual(transition('Ship after confirmation', 'NO')[0], 'cancel_requested')
        self.assertEqual(transition('Ship after confirmation', 'When will it arrive?')[0], 'needs_clarification')
        self.assertEqual(transition('Ship after confirmation', 'random text')[0], 'needs_clarification')

    def test_prepaid_flow(self):
        self.assertEqual(transition('Nudge to prepaid', 'PAY')[0], 'awaiting_payment')
        self.assertEqual(transition('Nudge to prepaid', 'paid', 'awaiting_payment')[0], 'awaiting_payment')
        self.assertEqual(transition('Nudge to prepaid', 'COD')[0], 'awaiting_cod_confirmation')
        self.assertEqual(transition('Nudge to prepaid', 'YES', 'awaiting_cod_confirmation')[0], 'confirmed')

    def test_timeout(self):
        self.assertIn('reminder', timeout(20, self.cfg))
        self.assertIn('manual review', timeout(24, self.cfg))

    def test_identity_and_pincode(self):
        self.assertTrue(review('asdf', 'House 14 near SBI Bank Station Road', '110001')['flags'])
        self.assertTrue(review('Anita Sharma', 'House 14 near SBI Bank Station Road', '000001')['flags'])
        self.assertFalse(review('Anita Sharma', 'House 14 near SBI Bank Station Road', '110001')['flags'])

    def test_invalid_identity_holds(self):
        order = {'customer_name':'asdf','address':'House 14 near SBI Bank Station Road','pincode':'110001','order_value':649,'customer_prior_orders':0,'customer_prior_rto':0,'utm_source':'direct'}
        self.assertEqual(decide(order, self.df, self.cfg)['action'], 'Hold / cancel')

    def test_chronological_no_target_leakage(self):
        sample = self.df.iloc[:3].copy()
        first = evaluate(sample, self.cfg)
        changed = sample.copy()
        changed.loc[0, 'status'] = 'RTO' if sample.loc[0, 'status'] == 'DELIVERED' else 'DELIVERED'
        second = evaluate(changed, self.cfg)
        # The first order has no earlier observed outcomes, so its own label cannot change its score.
        self.assertEqual(first.loc[0, 'risk'], second.loc[0, 'risk'])
        # Its changed label may affect later orders, but never its own prediction.
        self.assertEqual(first.loc[0, 'historical_cohort_n'], 0)

    def test_evaluation_is_time_ordered(self):
        sample = self.df.iloc[:10].sample(frac=1, random_state=4)
        scored = evaluate(sample, self.cfg)
        self.assertTrue(pd.to_datetime(scored.order_datetime).is_monotonic_increasing)

    def test_financial_scenario_components(self):
        scored = evaluate(self.df.iloc[:50], self.cfg)
        result = financial_scenario(scored, self.cfg)
        self.assertAlmostEqual(result['net_incremental_value'], result['rto_costs_avoided'] + result['incremental_delivered_contribution'] - result['genuine_contribution_at_risk_if_held_orders_cancelled'] - result['prepaid_discounts'])
        self.assertIn('nonresponders', result['assumptions'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
