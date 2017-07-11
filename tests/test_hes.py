"""Test for the hes module"""
#from unittest import TestCase
import unittest
import zeep

from hes import hes

class HesTest(unittest.TestCase):
    
    def setUp(self):
        self.building_info={'user_key':'ce4cdc28710349a1bbb4b7a047b65837','building_id':'142543'}
        
    def test_client_connectivity(self):
        client = hes.connect_client()
        self.assertIsInstance(client, zeep.Client)
        
    def test_succesful_completion(self):
        score = hes.hes_helix(self.building_info)
        print score
        
        self.assertEqual(score['base_score'], 6)
    
    def test_fail_bad_bulding_id(self):
        self.building_info['building_id'] = '999999'
        with self.assertRaises(TypeError):
            hes.test_client(self.building_info)
        
#          self.assertTrue(isinstance(s, basestring))
