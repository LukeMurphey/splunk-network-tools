# coding=utf-8
import unittest
import sys
import os
import json
import collections

sys.path.append( os.path.join("..", "src", "bin") )

from network_tools_app import ping, traceroute, whois, nslookup
from network_tools_app.flatten import flatten, flatten_to_table

class TestPing(unittest.TestCase):
    
    def test_do_ping(self):
        output, return_code, parsed = ping("127.0.0.1", count=3)
        
        self.assertEquals(return_code, 0)
        self.assertGreater(len(output), 0)
        self.assertEquals(int(parsed['received']), 3)
        
    def test_do_ping_error(self):
        output, return_code, _ = ping("doesnotexist", count=3)
        
        self.assertNotEquals(return_code, 0)
        self.assertGreater(len(output), 0)
        
class TestTraceroute(unittest.TestCase):
    
    def test_do_traceroute(self):
        _, _, parsed = traceroute("att.com")
        
        self.assertGreater(len(parsed), 0)
        
class TestWhois(unittest.TestCase):
    
    def test_do_whois(self):
        output = whois('173.255.235.229')
        
        self.assertGreater(len(output), 0)
        
    def test_do_whois_domain(self):
        output = whois('textcritical.net')
        
        self.assertGreater(len(output), 0)
        
class TestNSLookup(unittest.TestCase):
    
    def test_do_lookup(self):
        output = nslookup('textcritical.net')
        
        print output
        
        self.assertGreater(len(output), 0)
        
class TestFlatten(unittest.TestCase):
    
    def test_flatten_dict(self):
        
        d = '{ "name" : "Test", "configuration" : { "views" : [ { "name" : "some_view", "app" : "some_app" } ], "delay" : 300, "delay_readable" : "5m", "hide_chrome" : true, "invert_colors" : true }, "_user" : "nobody", "_key" : "123456789" }'
        flattened_d = flatten(json.loads(d))
        
        self.assertEquals(flattened_d['configuration.delay'], '300')
        self.assertEquals(flattened_d['configuration.views.0.name'], 'some_view')
        self.assertEquals(flattened_d['name'], "Test")
        
    def test_flatten_dict_to_table(self):
        
        d = '{ "name" : "Test", "configuration" : { "views" : [ { "name" : "some_view", "app" : "some_app" } ], "delay" : 300, "delay_readable" : "5m", "hide_chrome" : true, "invert_colors" : true }, "_user" : "nobody", "_key" : "123456789" }'
        flattened_d = flatten_to_table(json.loads(d))
        
        self.assertGreaterEqual(len(flattened_d[0]['attribute']), 1)
        self.assertGreaterEqual(len(str(flattened_d[0]['value'])), 1)
        
    def test_flatten_dict_ignore_blanks(self):
        
        d = collections.OrderedDict()
        
        d['not_blank'] = 'something here'
        d['none'] = None
        d['empty'] = ''
        
        flattened_d = flatten(d, ignore_blanks=True)
        
        self.assertEqual(flattened_d['not_blank'], 'something here')
        self.assertEqual('none' in flattened_d, False)
        self.assertEqual('empty' in flattened_d, False)
        
    def test_flatten_dict_array_mv(self):
        
        d = '{ "name" : "Test", "configuration" : ["a", "b", "c"] }'
        flattened = flatten(json.loads(d))
        
        self.assertGreaterEqual(len(flattened['configuration']), 3)
        
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suites = []
    suites.append(loader.loadTestsFromTestCase(TestPing))
    suites.append(loader.loadTestsFromTestCase(TestTraceroute))
    suites.append(loader.loadTestsFromTestCase(TestWhois))
    suites.append(loader.loadTestsFromTestCase(TestFlatten))
    suites.append(loader.loadTestsFromTestCase(TestNSLookup))

    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(suites))