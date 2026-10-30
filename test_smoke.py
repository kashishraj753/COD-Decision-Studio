import unittest
import pandas as pd
from engine import clean,decide,config
from address_review import review
from whatsapp import reply,timeout
from llm_review import interpret
class Smoke(unittest.TestCase):
 def setUp(self):self.df=clean(pd.read_csv('orders_sample.csv'));self.cfg=config()
 def test_data(self):self.assertEqual(len(self.df),2017);self.assertEqual(self.df.status.eq('RTO').sum(),573)
 def test_order(self):
  o={'customer_name':'Anita Sharma','address':'House 14 near SBI Bank Station Road','pincode':'110001','order_value':649,'customer_prior_orders':0,'customer_prior_rto':0,'utm_source':'direct'}
  self.assertIn(decide(o,self.df,self.cfg)['action'],['Ship as-is','Ship after confirmation','Nudge to prepaid','Hold / cancel'])
 def test_bad_name(self):self.assertTrue(review('asdf','House 14 near SBI Bank Station Road','110001')['flags'])
 def test_yes(self):self.assertIn('CONFIRMED',reply('Ship after confirmation','YES'))
 def test_timeout(self):self.assertIn('manual review',timeout(24,self.cfg))
if __name__=='__main__':unittest.main()
