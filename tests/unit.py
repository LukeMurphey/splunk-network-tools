# coding=utf-8
import unittest
import sys
import os
import json
import collections

sys.path.append( os.path.join("..", "src", "bin") )

from network_tools_app import ping, traceroute, whois, nslookup
from network_tools_app.flatten import flatten, flatten_to_table
from network_tools_app import pingparser

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
        
class TestPingParser(unittest.TestCase):
    
    def test_windows_parse(self):
        
        output = """Pinging 127.0.0.1 with 32 bytes of data:
Reply from 127.0.0.1: bytes=32 time<1ms TTL=128
Reply from 127.0.0.1: bytes=32 time<1ms TTL=128
Reply from 127.0.0.1: bytes=32 time<1ms TTL=128

Ping statistics for 127.0.0.1:
    Packets: Sent = 3, Received = 3, Lost = 0 (0% loss),
Approximate round trip times in milli-seconds:
    Minimum = 0ms, Maximum = 0ms, Average = 0ms
        """
        
        parsed = pingparser.parse(output)
          
        self.assertEquals(parsed['host'], '127.0.0.1')
        self.assertEquals(parsed['sent'], '3')
        self.assertEquals(parsed['received'], '3')
        self.assertEquals(parsed['packet_loss'], '0')
        
        self.assertEquals(parsed['min_ping'], '0')
        self.assertEquals(parsed['avg_ping'], '0')
        self.assertEquals(parsed['max_ping'], '0')
        self.assertEquals(parsed['jitter'], None)
        
    def test_osx_parse(self):
        
        output = """
PING 127.0.0.1 (127.0.0.1): 56 data bytes
64 bytes from 127.0.0.1: icmp_seq=0 ttl=64 time=0.052 ms
64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.136 ms
64 bytes from 127.0.0.1: icmp_seq=2 ttl=64 time=0.080 ms

--- 127.0.0.1 ping statistics ---
3 packets transmitted, 3 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 0.052/0.089/0.136/0.035 ms
        """
        
        parsed = pingparser.parse(output)
        
        self.assertEquals(parsed['host'], '127.0.0.1')
        self.assertEquals(parsed['sent'], '3')
        self.assertEquals(parsed['received'], '3')
        self.assertEquals(parsed['packet_loss'], '0.0')
        
        self.assertEquals(parsed['min_ping'], '0.052')
        self.assertEquals(parsed['avg_ping'], '0.089')
        self.assertEquals(parsed['max_ping'], '0.136')
        self.assertEquals(parsed['jitter'], '0.035')
        
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suites = []
    #suites.append(loader.loadTestsFromTestCase(TestPing))
    suites.append(loader.loadTestsFromTestCase(TestPingParser))
    #suites.append(loader.loadTestsFromTestCase(TestTraceroute))
    #suites.append(loader.loadTestsFromTestCase(TestWhois))
    #suites.append(loader.loadTestsFromTestCase(TestFlatten))
    #suites.append(loader.loadTestsFromTestCase(TestNSLookup))

    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(suites))