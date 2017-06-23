"""Test for the hes module"""
#from unittest import TestCase
import unittest

from hes import hes

class HesTest(unittest.TestCase):
    
    def setUp(self):
        self.building_info={'user_key':'ce4cdc28710349a1bbb4b7a047b65837','building_id':'142543'}
    
    def test_is_string(self):
        print self
        s = hes.test()
        print s
        self.assertTrue(isinstance(s, basestring))
        
    def test_client_connectivity(self):
        result = hes.test_client(self.building_info)
        self.assertEqual(result['result'],'OK')
