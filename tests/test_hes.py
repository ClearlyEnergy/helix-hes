"""Test for the hes module"""
import unittest
import zeep
import os
import datetime
import base64

from hes import hes


class HesTest(unittest.TestCase):

    def setUp(self):
        # This information is likely to change or become outdated as the hes
        # api updates or acount information is changed. If a lot of tests
        # start failing, make sure this is up to date.
        self.user_key = os.environ.get('HES_USER_KEY','')
        self.user_name = os.environ.get('HES_USER_NAME','')
        self.password = os.environ.get('HES_PASSWORD','')
        self.building_id = '142860' #sandbeta -- not current
#        self.building_id = '332297' #production -  if necessary check for new building @ https://hescore.labworks.org/dashboard
        self.client_url = 'https://sandbox.hesapi.labworks.org/st_api/wsdl' #sandbox
#        self.client_url = 'https://sandbeta.hesapi.labworks.org/st_api/wsdl' #sandbeta # DO NOT USE
#        self.client_url = 'https://hesapi.labworks.org/st_api/wsdl' #production

        self.hes_client = hes.HesHelix(self.client_url, self.user_name, self.password, self.user_key)

    def test_client_connectivity(self):
        self.assertIsInstance(self.hes_client.client, zeep.Client)

    def test_succesful_completion(self):
        score = self.hes_client.query_hes(self.building_id)
        self.assertEqual(score['Green Assessment Property Metric'], 4)

    def test_fail_bad_bulding_id(self):
        result = self.hes_client.query_hes(111111)
        self.assertTrue(result['status'],'error')
        
    def test_succesful_create(self):
        module_path = os.path.abspath(os.path.dirname(__file__))
        f_hpxml = open(module_path+"/house1.hpxml", "r")
        f_bytes = f_hpxml.read().encode("utf-8")
        self.hes_client.hpxml = base64.standard_b64encode(f_bytes)
        result = self.hes_client.submit_hpxml_inputs()
        self.assertTrue(result['result'],'OK')
        
#    def test_query_by_partner(self):
#        result=self.hes_client.query_by_partner('Test', datetime.date.today() - datetime.timedelta(30))
#        self.assertTrue(result['status'],'success')
#        self.assertTrue(len(result['building_ids'])>0)
            