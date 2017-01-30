# coding=utf-8
import unittest
import sys
import os

sys.path.append( os.path.join("..", "src", "bin") )

from network_tools_app import ping, traceroute

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
        output, return_code, parsed = traceroute("google.com")
        
        #self.assertNotEquals(parsed, 0)
        self.assertGreater(len(parsed), 0)
        
        import pprint
        pprint.pprint(parsed)
        #print parsed
        
if __name__ == "__main__":
    loader = unittest.TestLoader()
    suites = []
    suites.append(loader.loadTestsFromTestCase(TestPing))
    suites.append(loader.loadTestsFromTestCase(TestTraceroute))

    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(suites))