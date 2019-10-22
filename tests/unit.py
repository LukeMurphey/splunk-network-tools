# coding=utf-8
'''
The following test cases are included:

* TestPing
* TestTraceroute
* TestWhois
* TestNSLookup
* TestFlatten
* TestDictTranslate
* TestPingParser
* TestTracerouteParser
* TestTCPPing
* TestPingNetwork
'''

import unittest
import sys
import os
import json
import errno
import collections

sys.path.append(os.path.join("..", "src", "bin"))

from network_tools_app import ping, traceroute, whois, nslookup, tcp_ping
from network_tools_app.dict_translate import translate, is_array, merge_values, translate_key, prepare_translation_rules
from network_tools_app.flatten import flatten, flatten_to_table
from network_tools_app import pingparser, tracerouteparser
from network_tools_app.ping_network import ping_all, tcp_ping_all
from network_tools_app.portscan import port_scan
from network_tools_app.parseintset import parseIntSet
from portscan import PortRangeField

class TestPing(unittest.TestCase):

    def test_do_ping(self):
        """
        Perform a ping against a host that is known to exist.
        """

        output, return_code, parsed = ping("127.0.0.1", count=3)

        self.assertEqual(return_code, 0)
        self.assertGreater(len(output), 0)
        self.assertEqual(int(parsed['received']), 3)

    def test_do_ping_error(self):
        """
        Perform a ping against a host that doesn't exist
        """

        output, return_code, _ = ping("doesnotexist", count=3)

        self.assertNotEqual(return_code, 0)
        self.assertGreater(len(output), 0)

class TestTraceroute(unittest.TestCase):
    """
    This tests traceroute functionality which facilitates performing a traceroute and returning
    the raw results.
    """

    def test_do_traceroute(self):
        """
        Perform a traceroute and ensure the reults are valid.
        """
        _, _, parsed = traceroute("att.com")

        self.assertGreater(len(parsed), 0)

class TestWhois(unittest.TestCase):
    """
    This tests the whois functionality which performs whois requests on IPs and domain names.
    """

    def test_do_whois(self):
        """
        Test an IP whois
        """
        output = whois('173.255.235.229')

        self.assertGreater(len(output), 0)

    def test_do_whois_domain(self):
        """
        Test a domain whois
        """

        output = whois('textcritical.net')

        self.assertGreater(len(output), 0)

class TestNSLookup(unittest.TestCase):
    """
    Tests nslookup functionality which kicks off an nslookup using network_tools_app::nslookup.
    """

    def test_do_nslookup(self):
        """
        Test performing an nslookup.
        """

        output = nslookup('google.com')

        self.assertGreater(len(output), 0)

    def test_do_nslookup_bug_2480(self):
        """
        Test performing an nslookup on a domain that is recognized as IPv6.
        """

        output = nslookup('textcritical.net')

        self.assertGreater(len(output), 0)

    def test_do_nslookup_reverse(self):
        """
        Test performing an nslookup.
        """

        output = nslookup('172.217.6.14')

        self.assertGreater(len(output), 0)

class TestFlatten(unittest.TestCase):
    """
    Test the flatten module which converts a Python object to a flat dictionary.
    """

    def test_flatten_dict(self):
        """
        This tests conversion to a dictionary where the heirarchy is listed in the field names.
        """

        heirarchy = '{ "name" : "Test", "configuration" : { "views" : [ { "name" : "some_view", "app" : "some_app" } ], "delay" : 300, "delay_readable" : "5m", "hide_chrome" : true, "invert_colors" : true }, "_user" : "nobody", "_key" : "123456789" }'
        flat_list = flatten(json.loads(heirarchy))

        self.assertEqual(flat_list['configuration.delay'], '300')
        self.assertEqual(flat_list['configuration.views.0.name'], 'some_view')
        self.assertEqual(flat_list['name'], "Test")

    def test_flatten_dict_to_table(self):
        """
        This tests conversion to a table in which the name and value are put into separate fields.
        """

        heirarchy = '{ "name" : "Test", "configuration" : { "views" : [ { "name" : "some_view", "app" : "some_app" } ], "delay" : 300, "delay_readable" : "5m", "hide_chrome" : true, "invert_colors" : true }, "_user" : "nobody", "_key" : "123456789" }'
        flattened_d = flatten_to_table(json.loads(heirarchy))

        self.assertGreaterEqual(len(flattened_d[0]['attribute']), 1)
        self.assertGreaterEqual(len(str(flattened_d[0]['value'])), 1)

    def test_flatten_dict_ignore_blanks(self):
        """
        This tests the conversion but with the dropping of blank entries.
        """

        dictionary = collections.OrderedDict()

        dictionary['not_blank'] = 'something here'
        dictionary['none'] = None
        dictionary['empty'] = ''

        flattened_d = flatten(dictionary, ignore_blanks=True)

        self.assertEqual(flattened_d['not_blank'], 'something here')
        self.assertEqual('none' in flattened_d, False)
        self.assertEqual('empty' in flattened_d, False)

    def test_flatten_dict_array_mv(self):
        """
        This tests the conversion to ensure that a list is included within a single row.
        """

        dictionary = '{ "name" : "Test", "configuration" : ["a", "b", "c"] }'
        flattened = flatten(json.loads(dictionary))

        self.assertGreaterEqual(len(flattened['configuration']), 3)

class TestDictTranslate(unittest.TestCase):
    """
    Test the dict_translate module which converts a Python object to a flat dictionary.
    """

    def test_translate_remove_parts(self):
        """
        This tests conversion of field names.
        """

        dictionary = {
            'objects.LINOD.contact.name' : 'Luke Murphey'
        }

        translation_rules = [
            ('objects.*.contact.name', 'contact.name'),
        ]

        translated_dict = translate(dictionary, translation_rules)

        self.assertEqual(translated_dict['contact.name'], 'Luke Murphey')

    def test_is_array(self):
        """
        This tests whether or the item is an array.
        """

        self.assertEqual(is_array([]), True)
        self.assertEqual(is_array("almost an array"), False)
        self.assertEqual(is_array(u"almost an array"), False)
        self.assertEqual(is_array(['A']), True)
        self.assertEqual(is_array(None), False)

    def test_merge_values_one_none(self):
        self.assertEqual(merge_values(['A'], None), ['A'])
        self.assertEqual(merge_values(None, ['A']), ['A'])

    def test_merge_values_one_array(self):
        self.assertEqual(merge_values(['A'], 'B'), ['A', 'B'])
        self.assertEqual(merge_values('A', ['B']), ['A', 'B'])

    def test_merge_values_both_arrays(self):
        self.assertEqual(merge_values(['A', 'B'], ['C', 'D']), ['A', 'B', 'C', 'D'])

    def test_translate_key_escaped(self):
        translation_rules = [
            ('objects\\..*\\.contact\\.name', 'contact.name'),
        ]

        self.assertEqual(translate_key('objects.LINOD.contact.name', translation_rules), 'contact.name')

    def test_translate_key2(self):
        translation_rules = [
            ('AAAAA.*BBBBB', 'contact.name'),
        ]

        self.assertEqual(translate_key('AAAAAcontactBBBBB', translation_rules), 'contact.name')

    def test_prepare_translation_rules(self):
        translation_rules = [
            ('objects.*.contact.name', 'contact.name'),
        ]

        self.assertEqual(prepare_translation_rules(translation_rules)[0][0], 'objects\\..*\\.contact\\.name')

class TestPingParser(unittest.TestCase):
    """
    Test the class to parse the output of the ping command.
    """

    def test_windows_parse_localhost(self):
        """
        Test parsing a ping on Windows by IP (to localhost).
        """

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

        self.assertEqual(parsed['host'], '127.0.0.1')
        self.assertEqual(parsed['sent'], '3')
        self.assertEqual(parsed['received'], '3')
        self.assertEqual(parsed['packet_loss'], '0')

        self.assertEqual(parsed['min_ping'], '0')
        self.assertEqual(parsed['avg_ping'], '0')
        self.assertEqual(parsed['max_ping'], '0')
        self.assertEqual(parsed['jitter'], None) # Windows ping currently doesn't include jitter

    def test_windows_parse_domain(self):
        """
        Test parsing a ping on Windows to a domain name.
        """

        output = """
Pinging google.com [74.125.202.100] with 32 bytes of data:
Reply from 74.125.202.100: bytes=32 time=45ms TTL=44
Reply from 74.125.202.100: bytes=32 time=45ms TTL=44
Reply from 74.125.202.100: bytes=32 time=45ms TTL=44
Reply from 74.125.202.100: bytes=32 time=45ms TTL=44

Ping statistics for 74.125.202.100:
    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),
Approximate round trip times in milli-seconds:
    Minimum = 45ms, Maximum = 45ms, Average = 45ms
        """

        parsed = pingparser.parse(output)

        self.assertEqual(parsed['host'], 'google.com')
        self.assertEqual(parsed['sent'], '4')
        self.assertEqual(parsed['received'], '4')
        self.assertEqual(parsed['packet_loss'], '0')

        self.assertEqual(parsed['min_ping'], '45')
        self.assertEqual(parsed['avg_ping'], '45')
        self.assertEqual(parsed['max_ping'], '45')
        self.assertEqual(parsed['jitter'], None) # Windows ping currently doesn't include jitter

    def test_windows_parse_host_half_unreachable(self):
        """
        Test parsing a ping on Windows that returns host not reachable but only for some events.
        """

        output = """
Pinging 10.0.1.15 with 32 bytes of data:
Request timed out.
Request timed out.
Reply from 10.0.1.14: Destination host unreachable.
Reply from 10.0.1.14: Destination host unreachable.

Ping statistics for 10.0.1.15:
    Packets: Sent = 4, Received = 2, Lost = 2 (50% loss),
        """

        parsed = pingparser.parse(output)

        self.assertEqual(parsed['host'], '10.0.1.15')
        self.assertEqual(parsed['sent'], '4')
        self.assertEqual(parsed['received'], '2')
        self.assertEqual(parsed['packet_loss'], '50')

        self.assertEqual(parsed['min_ping'], 'NA')
        self.assertEqual(parsed['avg_ping'], 'NA')
        self.assertEqual(parsed['max_ping'], 'NA')

    def test_windows_parse_host_unreachable(self):
        """
        Test parsing a ping on Windows that returns host not reachable.
        """

        output = """
Pinging 10.0.1.15 with 32 bytes of data:
Reply from 10.0.1.14: Destination host unreachable.
Reply from 10.0.1.14: Destination host unreachable.
Reply from 10.0.1.14: Destination host unreachable.
Reply from 10.0.1.14: Destination host unreachable.

Ping statistics for 10.0.1.15:
    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),
        """

        parsed = pingparser.parse(output)

        self.assertEqual(parsed['host'], '10.0.1.15')
        self.assertEqual(parsed['sent'], '4')

        # The following two fields accurately represent what Windows ping returns but I don't
        # think they really make sense. This ought to 100% loss and 0 packets received.
        # In other words, this test is valid but Windows ping is not in my opinion.
        self.assertEqual(parsed['received'], '4')
        self.assertEqual(parsed['packet_loss'], '0')

        self.assertEqual(parsed['min_ping'], 'NA')
        self.assertEqual(parsed['avg_ping'], 'NA')
        self.assertEqual(parsed['max_ping'], 'NA')

    def test_osx_parse(self):
        """
        Test parsing ping output on OSX.
        """

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

        self.assertEqual(parsed['host'], '127.0.0.1')
        self.assertEqual(parsed['sent'], '3')
        self.assertEqual(parsed['received'], '3')
        self.assertEqual(parsed['packet_loss'], '0.0')

        self.assertEqual(parsed['min_ping'], '0.052')
        self.assertEqual(parsed['avg_ping'], '0.089')
        self.assertEqual(parsed['max_ping'], '0.136')
        self.assertEqual(parsed['jitter'], '0.035')

class TestTracerouteParser(unittest.TestCase):
    """
    Test parsing of traceroute output.
    """

    def test_windows_parse(self):
        """
        Test parsing Windows traceroute.
        """

        output = """Tracing route to att.com [144.160.155.43] over a maximum of 30 hops:

  1    18 ms    <1 ms    <1 ms  10.0.0.1
  2    14 ms    14 ms    14 ms  192.168.1.254
  3     *        *        *     Request timed out.
  4    34 ms    34 ms    47 ms  71.145.65.194
  5     *        *       44 ms  71.145.64.128
  6    40 ms    36 ms    38 ms  12.83.43.45
  7   107 ms    84 ms    83 ms  gar2.placa.ip.att.net [12.122.110.5]
  8    86 ms    86 ms    86 ms  12.91.205.18
  9    87 ms    73 ms    73 ms  att.com [144.160.155.43]

Trace complete."""

        parsed_output = tracerouteparser.Traceroute.parse(output, True)

        # Verify the destination
        self.assertEqual(parsed_output.dest, "att.com")
        self.assertEqual(parsed_output.dest_ip, "144.160.155.43")

        # Verify the hops
        self.assertEqual(len(parsed_output.hops), 9)

        # Hop 1
        self.assertEqual(parsed_output.hops[0].number, 1)
        self.assertEqual(len(parsed_output.hops[0].probes), 3)
        self.assertEqual(parsed_output.hops[0].probes[0].rtt, 18)
        self.assertEqual(parsed_output.hops[0].probes[1].rtt, 1)
        self.assertEqual(parsed_output.hops[0].probes[2].rtt, 1)

        self.assertEqual(parsed_output.hops[0].probes[1].dest_ip, '10.0.0.1')
        self.assertEqual(parsed_output.hops[0].probes[1].dest, '10.0.0.1')

        # Hop 3 (request timed out)
        self.assertEqual(parsed_output.hops[2].number, 3)
        self.assertEqual(len(parsed_output.hops[2].probes), 3)
        self.assertEqual(parsed_output.hops[2].probes[0].rtt, None)
        self.assertEqual(parsed_output.hops[2].probes[1].rtt, None)
        self.assertEqual(parsed_output.hops[2].probes[2].rtt, None)

        self.assertEqual(parsed_output.hops[2].probes[1].dest_ip, None)
        self.assertEqual(parsed_output.hops[2].probes[1].dest, None)

        # Hop 7 (has DNS)
        self.assertEqual(parsed_output.hops[6].number, 7)
        self.assertEqual(len(parsed_output.hops[6].probes), 3)
        self.assertEqual(parsed_output.hops[6].probes[0].rtt, 107)
        self.assertEqual(parsed_output.hops[6].probes[1].rtt, 84)
        self.assertEqual(parsed_output.hops[6].probes[2].rtt, 83)

        self.assertEqual(parsed_output.hops[6].probes[1].dest, 'gar2.placa.ip.att.net')
        self.assertEqual(parsed_output.hops[6].probes[1].dest_ip, '12.122.110.5')

    def test_windows_parse_unreachable(self):
        """
        Test parsing Windows traceroute.
        """

        output = """Tracing route to att.com [144.160.36.42]    
over a maximum of 30 hops:

  1    <1 ms    <1 ms    <1 ms  10.0.0.1
  2    15 ms    14 ms    14 ms  192.168.1.254
  3     *        *        *     Request timed out.
  4    34 ms    33 ms    33 ms  71.145.65.194
  5    43 ms    58 ms    92 ms  12.83.43.49
  6    88 ms    66 ms    90 ms  ggr1.chail.ip.att.net [12.122.132.181]
  7   125 ms    42 ms    41 ms  12.249.81.194
  8  att.com [144.160.36.42]  reports: Destination protocol unreachable.

Trace complete."""

        parsed_output = tracerouteparser.Traceroute.parse(output, True)

        # Verify the destination
        self.assertEqual(parsed_output.dest, "att.com")
        self.assertEqual(parsed_output.dest_ip, "144.160.36.42")

        # Verify the hops
        self.assertEqual(len(parsed_output.hops), 8)

        # Hop 1
        self.assertEqual(parsed_output.hops[0].number, 1)
        self.assertEqual(len(parsed_output.hops[0].probes), 3)
        self.assertEqual(parsed_output.hops[0].probes[0].rtt, 1)
        self.assertEqual(parsed_output.hops[0].probes[1].rtt, 1)
        self.assertEqual(parsed_output.hops[0].probes[2].rtt, 1)

        self.assertEqual(parsed_output.hops[0].probes[1].dest_ip, '10.0.0.1')
        self.assertEqual(parsed_output.hops[0].probes[1].dest, '10.0.0.1')

        # Hop 3 (request timed out)
        self.assertEqual(parsed_output.hops[2].number, 3)
        self.assertEqual(len(parsed_output.hops[2].probes), 3)
        self.assertEqual(parsed_output.hops[2].probes[0].rtt, None)
        self.assertEqual(parsed_output.hops[2].probes[1].rtt, None)
        self.assertEqual(parsed_output.hops[2].probes[2].rtt, None)

        self.assertEqual(parsed_output.hops[2].probes[1].dest_ip, None)
        self.assertEqual(parsed_output.hops[2].probes[1].dest, None)

        # Hop 8 (unreachable)
        self.assertEqual(parsed_output.hops[7].number, 8)
        self.assertEqual(len(parsed_output.hops[7].probes), 1)

        self.assertEqual(parsed_output.hops[7].probes[0].dest, 'att.com')
        self.assertEqual(parsed_output.hops[7].probes[0].dest_ip, '144.160.36.42')

    def test_osx_parse_oddities(self):
        """
        This tests traceroute output when it contains some strange things like N! which apparently
        means that there is an outage (see https://www.webmasterworld.com/forum23/2238.htm).

        This also includes a warning which indicates that the destination has multiple addresses.
        """

        output = """
traceroute: Warning: att.com has multiple addresses; using 144.160.36.42
traceroute to att.com (144.160.36.42), 64 hops max, 52 byte packets
 1  win-ad.demo.net (10.0.0.1)  1.709 ms  1.024 ms  0.743 ms
 2  192.168.1.254 (192.168.1.254)  15.484 ms  16.503 ms  15.885 ms
 3  162-235-240-3.lightspeed.cicril.sbcglobal.net (162.235.240.3)  35.881 ms  36.367 ms  35.004 ms
 4  71.145.65.194 (71.145.65.194)  35.976 ms  35.911 ms  36.732 ms
 5  12.83.43.49 (12.83.43.49)  38.070 ms
    12.83.43.53 (12.83.43.53)  38.454 ms
    12.83.43.49 (12.83.43.49)  39.049 ms
 6  ggr1.chail.ip.att.net (12.122.132.181)  36.673 ms  36.318 ms  36.972 ms
 7  12.249.81.194 (12.249.81.194)  43.967 ms  43.266 ms  43.693 ms
 8  my.atttest.com (144.160.36.42)  45.424 ms !N  44.528 ms !N  44.779 ms !N
        """

        parsed_output = tracerouteparser.Traceroute.parse(output, True)

        # Verify the destination
        self.assertEqual(parsed_output.dest, "att.com")
        self.assertEqual(parsed_output.dest_ip, "144.160.36.42")

        # Hop 1
        hop = parsed_output.hops[0]
        self.assertEqual(hop.number, 1)
        self.assertEqual(len(hop.probes), 3)
        self.assertEqual(hop.probes[0].rtt, 1.709)
        self.assertEqual(hop.probes[1].rtt, 1.024)
        self.assertEqual(hop.probes[2].rtt, 0.743)

        self.assertEqual(hop.probes[0].dest_ip, '10.0.0.1')
        self.assertEqual(hop.probes[0].dest, 'win-ad.demo.net')

        # Hop 8: missing probes
        hop = parsed_output.hops[7]
        self.assertEqual(hop.number, 8)
        self.assertEqual(len(hop.probes), 3)
        self.assertEqual(hop.probes[0].rtt, 45.424)
        self.assertEqual(hop.probes[1].rtt, 44.528)
        self.assertEqual(hop.probes[2].rtt, 44.779)

        self.assertEqual(hop.probes[0].dest_ip, '144.160.36.42')
        self.assertEqual(hop.probes[0].dest, 'my.atttest.com')

        self.assertEqual(hop.probes[1].dest_ip, '144.160.36.42')
        self.assertEqual(hop.probes[1].dest, 'my.atttest.com')

        self.assertEqual(hop.probes[2].dest_ip, '144.160.36.42')
        self.assertEqual(hop.probes[2].dest, 'my.atttest.com')

    def test_osx_parse(self):
        """
        Test parsing an OSX traceroute. Note that this traceroute includes multiple IPs
        on different lines for different addresses.
        """

        output = """traceroute to google.com (216.58.192.238), 64 hops max, 52 byte packets
 1  10.0.0.1 (10.0.0.1)  1.450 ms  0.967 ms  0.842 ms
 2  192.168.1.254 (192.168.1.254)  15.996 ms  15.873 ms  17.041 ms
 3  162-235-240-3.lightspeed.cicril.sbcglobal.net (162.235.240.3)  39.095 ms  35.661 ms  35.715 ms
 4  71.145.65.194 (71.145.65.194)  37.061 ms  37.974 ms  36.744 ms
 5  12.83.43.53 (12.83.43.53)  36.973 ms
    12.83.43.49 (12.83.43.49)  39.475 ms
    12.83.43.53 (12.83.43.53)  38.859 ms
 6  12.123.159.53 (12.123.159.53)  38.333 ms  38.525 ms  38.821 ms
 7  12.247.252.10 (12.247.252.10)  38.299 ms  40.987 ms *
 8  108.170.243.193 (108.170.243.193)  37.973 ms  37.021 ms *
 9  216.239.42.113 (216.239.42.113)  37.602 ms
    216.239.42.111 (216.239.42.111)  37.130 ms  38.387 ms
10  ord30s26-in-f14.1e100.net (216.58.192.238)  37.836 ms  38.070 ms  37.424 ms"""

        parsed_output = tracerouteparser.Traceroute.parse(output, True)

        # Verify the destination
        self.assertEqual(parsed_output.dest, "google.com")
        self.assertEqual(parsed_output.dest_ip, "216.58.192.238")

        # Hop 1
        hop = parsed_output.hops[0]
        self.assertEqual(hop.number, 1)
        self.assertEqual(len(hop.probes), 3)
        self.assertEqual(hop.probes[0].rtt, 1.45)
        self.assertEqual(hop.probes[1].rtt, 0.967)
        self.assertEqual(hop.probes[2].rtt, 0.842)

        self.assertEqual(hop.probes[0].dest_ip, '10.0.0.1')
        self.assertEqual(hop.probes[0].dest, '10.0.0.1')

        # Hop 3: domain name included
        hop = parsed_output.hops[2]
        self.assertEqual(hop.number, 3)
        self.assertEqual(len(hop.probes), 3)
        self.assertEqual(hop.probes[0].rtt, 39.095)
        self.assertEqual(hop.probes[1].rtt, 35.661)
        self.assertEqual(hop.probes[2].rtt, 35.715)

        self.assertEqual(hop.probes[0].dest_ip, '162.235.240.3')
        self.assertEqual(hop.probes[0].dest, '162-235-240-3.lightspeed.cicril.sbcglobal.net')

        # Hop 5: multiple hosts
        hop = parsed_output.hops[4]
        self.assertEqual(hop.number, 5)
        self.assertEqual(len(hop.probes), 3)
        self.assertEqual(hop.probes[0].rtt, 36.973)
        self.assertEqual(hop.probes[1].rtt, 39.475)
        self.assertEqual(hop.probes[2].rtt, 38.859)

        self.assertEqual(hop.probes[0].dest_ip, '12.83.43.53')
        self.assertEqual(hop.probes[0].dest, '12.83.43.53')

        self.assertEqual(hop.probes[1].dest_ip, '12.83.43.49')
        self.assertEqual(hop.probes[1].dest, '12.83.43.49')

        self.assertEqual(hop.probes[2].dest_ip, '12.83.43.53')
        self.assertEqual(hop.probes[2].dest, '12.83.43.53')

    def test_linux_parse(self):
        """
        Test parsing on Linux.
        """

        output = """
traceroute to edgecastcdn.net (72.21.81.13), 30 hops max, 38 byte packets
 1  *  *
 2  *  *
 3  *  *
 4  10.251.11.32 (10.251.11.32)  3574.616 ms  0.153 ms
 5  10.251.10.2 (10.251.10.2)  465.821 ms  2500.031 ms
 6  172.18.68.206 (172.18.68.206)  170.197 ms  78.979 ms
 7  172.18.59.165 (172.18.59.165)  151.123 ms  525.177 ms
 8  172.18.59.170 (172.18.59.170)  150.909 ms  172.18.59.174 (172.18.59.174)  62.591 ms
 9  172.18.75.5 (172.18.75.5)  123.078 ms  68.847 ms
10  12.91.11.5 (12.91.11.5)  79.834 ms  556.366 ms
11  cr2.ptdor.ip.att.net (12.123.157.98)  245.606 ms  83.038 ms
12  cr81.st0wa.ip.att.net (12.122.5.197)  80.078 ms  96.588 ms
13  gar1.omhne.ip.att.net (12.122.82.17)  363.800 ms  12.122.111.9 (12.122.111.9)  72.113 ms
14  206.111.7.89.ptr.us.xo.net (206.111.7.89)  188.965 ms  270.203 ms
15  xe-0-6-0-5.r04.sttlwa01.us.ce.gin.ntt.net (129.250.196.230)  706.390 ms  ae-6.r21.sttlwa01.us.bb.gin.ntt.net (129.250.5.44)  118.042 ms
16  xe-9-3-2-0.co1-96c-1b.ntwk.msn.net (207.46.47.85)  675.110 ms  72.21.81.13 (72.21.81.13)  82.306 ms

"""
        parsed_output = tracerouteparser.Traceroute.parse(output, True)

        # Verify the destination
        self.assertEqual(parsed_output.dest, "edgecastcdn.net")
        self.assertEqual(parsed_output.dest_ip, "72.21.81.13")

        # Verify the hops
        self.assertEqual(len(parsed_output.hops), 16)

        # Hop 1 (time out)
        self.assertEqual(parsed_output.hops[0].number, 1)
        self.assertEqual(len(parsed_output.hops[0].probes), 2)
        self.assertEqual(parsed_output.hops[0].probes[0].rtt, None)
        self.assertEqual(parsed_output.hops[0].probes[1].rtt, None)

        self.assertEqual(parsed_output.hops[0].probes[1].dest_ip, None)
        self.assertEqual(parsed_output.hops[0].probes[1].dest, None)

        # Hop 4
        self.assertEqual(parsed_output.hops[3].number, 4)
        self.assertEqual(len(parsed_output.hops[3].probes), 2)
        self.assertEqual(parsed_output.hops[3].probes[0].rtt, 3574.616)
        self.assertEqual(parsed_output.hops[3].probes[1].rtt, 0.153)

        self.assertEqual(parsed_output.hops[3].probes[1].dest_ip, '10.251.11.32')
        self.assertEqual(parsed_output.hops[3].probes[1].dest, '10.251.11.32')

        # Hop 8: multiple hosts
        self.assertEqual(parsed_output.hops[7].number, 8)
        self.assertEqual(len(parsed_output.hops[7].probes), 2)
        self.assertEqual(parsed_output.hops[7].probes[0].rtt, 150.909)
        self.assertEqual(parsed_output.hops[7].probes[1].rtt, 62.591)

        self.assertEqual(parsed_output.hops[7].probes[0].dest_ip, '172.18.59.170')
        self.assertEqual(parsed_output.hops[7].probes[0].dest, '172.18.59.170')

        self.assertEqual(parsed_output.hops[7].probes[1].dest_ip, '172.18.59.174')
        self.assertEqual(parsed_output.hops[7].probes[1].dest, '172.18.59.174')

        # Hop 15: multiple hosts with domain names
        hop = parsed_output.hops[14]
        self.assertEqual(hop.number, 15)
        self.assertEqual(len(hop.probes), 2)
        self.assertEqual(hop.probes[0].rtt, 706.390)
        self.assertEqual(hop.probes[1].rtt, 118.042)

        self.assertEqual(hop.probes[0].dest_ip, '129.250.196.230')
        self.assertEqual(hop.probes[0].dest, 'xe-0-6-0-5.r04.sttlwa01.us.ce.gin.ntt.net')

        self.assertEqual(hop.probes[1].dest_ip, '129.250.5.44')
        self.assertEqual(hop.probes[1].dest, 'ae-6.r21.sttlwa01.us.bb.gin.ntt.net')

class TestTCPPing(unittest.TestCase):
    """
    Test pinging using TCP.
    """

    def test_ping(self):
        result = tcp_ping('textcritical.net', port=80, count=5)
        print(result['output'])
        self.assertEqual(result['dest'], 'textcritical.net')
        self.assertEqual(result['sent'], 5)
        self.assertEqual(result['received'], 5)

        self.assertGreaterEqual(result['jitter'], 0)
        self.assertGreaterEqual(result['min_ping'], 0)
        self.assertGreaterEqual(result['max_ping'], 0)
        self.assertGreaterEqual(result['avg_ping'], 0)

class TestPingNetwork(unittest.TestCase):
    """
    Test pinging using TCP.
    """

    def test_tcp_ping_all(self):
        result = tcp_ping_all('textcritical.net', port=80, count=5)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['dest'], 'textcritical.net')
        self.assertEqual(result[0]['sent'], 5)
        self.assertEqual(result[0]['received'], 5)

        self.assertGreaterEqual(result[0]['jitter'], 0)
        self.assertGreaterEqual(result[0]['min_ping'], 0)
        self.assertGreaterEqual(result[0]['max_ping'], 0)
        self.assertGreaterEqual(result[0]['avg_ping'], 0)

class TestSplitIntSet(unittest.TestCase):
    """
    Test splitting of a list of integers.
    """

    def test_combination(self):
        result = parseIntSet("80-90,8443")

        self.assertEqual(len(result), 12)
        self.assertEqual(result, set([80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 8443]))

    def test_single(self):
        result = parseIntSet("80")

        self.assertEqual(len(result), 1)
        self.assertEqual(result, set([80]))

    def test_duplicates(self):
        result = parseIntSet("80-90,89")
        self.assertEqual(result, set([80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90]))

        self.assertEqual(len(result), 11)

    def test_extra_spaces(self):
        result = parseIntSet(" 80-90 , 8443 ")

        self.assertEqual(len(result), 12)
        self.assertEqual(result, set([80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 8443]))

    def test_error_reporting(self):
        with self.assertRaises(ValueError):
            parseIntSet("80-90 , tree", True)

        result = parseIntSet("80-81, tree")
        self.assertEqual(len(result), 2)
        self.assertEqual(result, set([80, 81]))

class TestPortScan(unittest.TestCase):
    """
    Test port scanning using TCP.
    """

    def test_port_scan(self):
        results = port_scan('textcritical.net', '80-81')
        self.assertEqual(len(results), 2)

    def test_port_scan_single(self):
        results = port_scan('textcritical.net', '80')
        self.assertEqual(len(results), 1)

        self.assertEqual(results[0]['status'], 'open')
        self.assertEqual(results[0]['dest'], 'textcritical.net')
        self.assertEqual(results[0]['port'], 'TCP\\80')

    def test_port_scan_preparsed(self):
        results = port_scan('textcritical.net', [80, 443])
        self.assertEqual(len(results), 2)

class TestPortRangeField(unittest.TestCase):
    """
    Test the port range field.
    """

    field = None

    def setUp(self):
        self.field = PortRangeField('name', 'title', 'description')

    def test_to_string(self):
        value = self.field.to_string([80, 443])

        self.assertEqual(value, "80,443")
    def test_to_python(self):
        value = self.field.to_python("80,443")

        self.assertEqual(value, set([80, 443]))

if __name__ == '__main__':
    unittest.main()
