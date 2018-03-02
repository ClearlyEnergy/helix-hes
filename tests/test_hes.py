"""Test for the hes module"""
import unittest
import zeep

from hes import hes


class HesTest(unittest.TestCase):

    def setUp(self):
        # This information is likely to change or become outdated as the hes
        # api updates or acount information is changed. If a lot of tests
        # start failing, make sure this is up to date.
        self.user_name = 'TST-HELIX'
        self.password = 'helix123'
#        self.user_key = '520df908c6cb4bea8c14691ee95aff88' #sandbeta
        self.user_key = '38681c487f054bfa9bb090cc93404e9f' #sandbox
#        self.building_id = '142860' #sandbeta
        self.building_id = '142543' #sandbox
        self.client_url = 'https://sandbox.hesapi.labworks.org/st_api/wsdl' #sandbox

        self.hes_client = hes.HesHelix(self.client_url, self.user_name, self.password, self.user_key)

    def test_client_connectivity(self):
        self.assertIsInstance(self.hes_client.client, zeep.Client)

    def test_succesful_completion(self):
        score = self.hes_client.query_hes(self.building_id)
        self.assertEqual(score['base_score'], 6)

    def test_fail_bad_bulding_id(self):
        result = self.hes_client.query_hes(111111)
        self.assertTrue(result['status'],'error')
            