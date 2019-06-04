"""
This module includes a series of functions for performing network operations (ping, traceroute, etc)
"""

# Update the sys.path so that libraries will be loaded out of the network_tools_app directory.
# This is important in order to make sure that app won't cause issues with other Splunk apps
# that may include these same libraries (since Splunk puts other apps on the sys.path which
# can make the apps override each other).
import sys
import os
import errno
import splunk.appserver.mrsparkle.lib.util as util

lib_dir = os.path.join(util.get_apps_dir(), 'network_tools', 'bin', 'network_tools_app')

if not lib_dir in sys.path:
    sys.path.append(lib_dir)

# App provided imports
from event_writer import StashNewWriter
import pyspeedtest
import pingparser
from tracerouteparser import Traceroute
from wakeonlan import wol
from ipwhois import IPWhois
from pythonwhois import get_whois
from flatten import flatten
from ipaddr import IPAddress
from dns import resolver,reversename
from portscan import port_scan

# Environment imports
from platform import system as system_name
import subprocess
import collections
import binascii
import json
from timeit import default_timer as timer
import socket

# Splunk imports
import splunk
import splunk.rest as rest
from splunk.models.base import SplunkAppObjModel
from splunk.models.field import Field

class CommandNotFoundException(Exception):
    """
    Represents the inability to run a command because it could not be found.
    """
    def __init__(self, command):
        super(CommandNotFoundException, self).__init__('Command could not be executed since it could not be found; make sure that "%s" is installed and in the environment\'s path' % (command))

class NetworkToolsConfig(SplunkAppObjModel):
    """
    Represents the network_tools.conf custom conf file.
    """

    resource = '/admin/network_tools'
    index = Field()

def get_app_config(session_key, stanza="default"):
    """
    Get the app configuration

    Arguments:
    session_key -- The session key to use when connecting to the REST API
    stanza -- The stanza to get the proxy information from (defaults to "default")
    """

    # If the stanza is empty, then just use the default
    if stanza is None or stanza.strip() == "":
        stanza = "default"
 
    # Get the configuration
    try:
        app_config = NetworkToolsConfig.get(NetworkToolsConfig.build_id(stanza, "network_tools", "nobody"), sessionKey=session_key)
    except splunk.ResourceNotFound:
        return None

    return app_config

def get_default_index(session_key):
    """
    Get the default index to output results to.
    """
    app_config = get_app_config(session_key)

    if app_config is None:
        return "default"
    else:
        return app_config.index

def traceroute(host, unique_id=None, index=None, sourcetype="traceroute",
               source="traceroute_search_command", logger=None, include_dest_info=True,
               include_raw_output=False):
    """
    Performs a traceroute using the the native traceroute command and returns the output in a
    parsed, machine-readable format.

    It will also write out the data into Splunk using a stash file if the index parameters is
    set to a value that is not None.
    """

    if system_name().lower() == "windows":
        cmd = ["tracert"]
    else:
        cmd = ["traceroute"]

    # Add the host argument
    cmd.append(host)

    # Run the traceroute command and get the output
    output = None
    return_code = None

    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return_code = 0
    except subprocess.CalledProcessError as exception:
        output = exception.output
        return_code = exception.returncode
    except OSError as exception:
        if exception.errno == errno.ENOENT:
            raise CommandNotFoundException(cmd[0])
        else:
            raise exception

    # Parse the output
    try:
        trp = Traceroute.parse(output)

        # This will contain the hops
        parsed = []

        hop_idx = 0

        # Make an entry for each hop
        for hop in trp.hops:

            if hop.probes is None or len(hop.probes) == 0:
                continue

            hop_idx = hop_idx + 1

            # This will track the probes
            rtts = []
            ips = []
            names = []

            hop_dict = collections.OrderedDict()
            hop_dict['hop'] = hop_idx

            for probe in hop.probes:

                if probe.rtt is not None:
                    rtts.append(str(probe.rtt))

                if probe.dest_ip is not None:
                    ips.append(probe.dest_ip)

                if probe.dest is not None:
                    names.append(probe.dest)

            hop_dict['rtt'] = rtts
            hop_dict['ip'] = ips
            hop_dict['name'] = names

            if include_dest_info:
                hop_dict['dest_ip'] = trp.dest_ip
                hop_dict['dest_host'] = trp.dest

            if include_raw_output:
                hop_dict['output'] = output

            parsed.append(hop_dict)

    except Exception:

        if logger:
            logger.exception("Unable to parse traceroute output")

        raise Exception("Unable to parse traceroute output")

    # Write the event as a stash new file
    if index is not None:
        writer = StashNewWriter(index=index, source_name=source, sourcetype=sourcetype,
                                file_extension=".stash_output")

        # Let's store the basic information for the traceroute that will be included with each hop
        proto = collections.OrderedDict()

        # Include the destination info if it was included already
        if not include_dest_info:
            proto['dest_ip'] = trp.dest_ip
            proto['dest_host'] = trp.dest

        if unique_id is None:
            unique_id = binascii.b2a_hex(os.urandom(4))

        proto['unique_id'] = unique_id

        for parsed_hop in parsed:

            result = collections.OrderedDict()
            result.update(parsed_hop)
            result.update(proto)

            # Log that we performed the traceroute
            if logger:
                logger.debug("Wrote stash file=%s", writer.write_event(result))

    return output, return_code, parsed

def tcp_ping(host, port=80, count=1, index=None, sourcetype="ping", source="ping_search_command", logger=None):
    """
    Pings the host using TCP and returns a tuple consisting of:

     1) the output string
     2) the return code (0 is the expected return code)
     3) parsed output from the ping command
    """
    sent = 0
    packet_loss = 0
    output = []
    received = 0
    response_times = []

    for i in range(0, count):
        success = False

        # New Socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 1 sec Timeout
        sock.settimeout(1)

        # Start a timer
        timer_start = timer()

        # Try to Connect
        try:
            sock.connect((host, int(port)))
            sent += 1
            sock.shutdown(socket.SHUT_RD)
            success = True
        
        # Connection Time Out
        except socket.timeout:
            output.append("Connection timeout to %s[%s]" % (host, port))
            sent += 1
            packet_loss += 1
        # Connection Time Out
        except OSError as e:
            output.append("Error when connecting to %s[%s]: %r" % (host, port, str(e)))
            sent += 1
            packet_loss += 1

        # Stop Timer
        timer_stop = timer()
        total_runtime = float("%.2f" % (1000 * (timer_stop - timer_start)))
        response_times.append(total_runtime)

        if success:
            output.append("Connected to %s[%s]: tcp_seq=%s time=%.2f ms" % (host, port, i, total_runtime))
            received += 1
    
    # Calculate the jitter
    diff = 0
    prev_response_time = None
    for response_time in response_times:
        if prev_response_time is not None:
            diff += abs(prev_response_time - response_time)
        
        prev_response_time = response_time

    jitter = (diff * 1.0) / len(response_times)

    # Calculate the min_ping, max_ping, avg_ping
    min_ping = None
    max_ping = None
    total = 0

    for response_time in response_times:
        # Figure out min_ping
        if min_ping is None:
            min_ping = response_time

        if response_time < min_ping:
            min_ping = response_time
    
        # Figure out max_ping
        if max_ping is None:
            max_ping = response_time

        if response_time > max_ping:
            max_ping = response_time

        # Total up the value for the average calculation
        total += response_time

    # Calculate the packet loss as a percent
    if sent > 0:
        packet_loss_percent = 100 * (packet_loss / sent)
    else:
        packet_loss_percent = 0

    avg_ping = total / len(response_times)

    output.append("\n--- %s ping statistics ---" % host)
    output.append("%i packets transmitted, %i packets received, %i%% packet loss" % (sent, received, packet_loss_percent))

    # Make the summary dictionary
    result = collections.OrderedDict()
    result['dest'] = host
    result['output'] = "\n".join(output)
    result['sent'] = sent
    result['received'] = received
    result['packet_loss'] = int(round(packet_loss_percent, 0))
    result['jitter'] = round(jitter, 2)
    result['min_ping'] = round(min_ping, 2)
    result['max_ping'] = round(max_ping, 2)
    result['avg_ping'] = round(avg_ping, 2)

    # Write the event as a stash new file
    if index is not None:
        writer = StashNewWriter(index=index, source_name=source, sourcetype=sourcetype,
                                file_extension=".stash_output")

        # Log that we performed the ping
        if logger:
            logger.debug("Wrote stash file=%s", writer.write_event(result))

    return result

def ping(host, count=1, index=None, sourcetype="ping", source="ping_search_command", logger=None):
    """
    Pings the host using the native ping command on the platform and returns a tuple consisting of:

     1) the output string
     2) the return code (0 is the expected return code)
     3) parsed output from the ping command
    """

    cmd = ["ping"]

    # Add the argument of the number of pings
    if system_name().lower() == "windows":
        cmd.extend(["-n", str(count)])
    else:
        cmd.extend(["-c", str(count)])

    # Add the host argument
    cmd.append(host)

    output = None
    return_code = None

    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return_code = 0
    except subprocess.CalledProcessError as exception:
        output = exception.output
        return_code = exception.returncode
    except OSError as exception:
        if exception.errno == errno.ENOENT:
            raise CommandNotFoundException(cmd[0])
        else:
            raise exception

    # Parse the output
    try:
        parsed = pingparser.parse(output)
    except Exception:
        parsed = {
            'message': 'output could not be parsed',
            'output': output
        }

    # Write the event as a stash new file
    if index is not None:
        writer = StashNewWriter(index=index, source_name=source, sourcetype=sourcetype,
                                file_extension=".stash_output")

        result = collections.OrderedDict()
        result.update(parsed)

        if 'host' in result:
            result['dest'] = result['host']
            del result['host']

        result['return_code'] = return_code
        result['output'] = output

        # Remove the jitter field on Windows since it doesn't get populated on Windows
        if 'jitter' in result and (result['jitter'] is None or len(result['jitter']) == 0):
            del result['jitter']

        # Log that we performed the ping
        if logger:
            logger.debug("Wrote stash file=%s", writer.write_event(result))

    return output, return_code, parsed

def speedtest(host, runs=2, index=None, sourcetype="speedtest", source="speedtest_search_command",
              logger=None):
    """
    Performs a bandwidth speedtest and sends the results to an index.
    """

    # This will contain the event we will index and return
    result = {}

    speedtester = pyspeedtest.SpeedTest(host=host, runs=runs)
    result['ping'] = round(speedtester.ping(), 2)

    result['download'] = round(speedtester.download(), 2)
    result['download_readable'] = pyspeedtest.pretty_speed(speedtester.download())

    result['upload'] = round(speedtester.upload(), 2)
    result['upload_readable'] = pyspeedtest.pretty_speed(speedtester.upload())

    result['server'] = speedtester.host

    # Write the event as a stash new file
    if index is not None:
        writer = StashNewWriter(index=index, source_name=source, sourcetype=sourcetype,
                                file_extension=".stash_output")

        # Log that we performed the speedtest
        if logger:
            logger.debug("Wrote stash file=%s", writer.write_event(result))

    # Return the result
    return result

def get_host(name, session_key, logger=None):
    """
    Get the host information object for the given name.
    """

    uri = '/servicesNS/nobody/network_tools/storage/collections/data/network_hosts'

    getargs = {
        'output_mode': 'json',
        'query' : '{"name":"' + name + '"}'
    }

    _, host_entry = rest.simpleRequest(uri, sessionKey=session_key, getargs=getargs,
                                       raiseAllErrors=True)

    host_entry = json.loads(host_entry)

    # Make sure we got at least one result
    if len(host_entry) > 0:
        if logger is not None:
            logger.debug("Successfully found an entry in the table of hosts for host=%s", name)

        return host_entry[0]

    else:
        if logger is not None:
            logger.warn("Failed to find an entry in the table of hosts for host=%s", name)

        return None

def wakeonlan(host, mac_address=None, ip_address=None, port=None, index=None,
              sourcetype="wakeonlan", source="wakeonlan_search_command", logger=None,
              session_key=None):
    """
    Performs a wake-on-LAN request.
    """

    # Resolve the MAC address (and port and IP address) if needed
    host_info = None

    if host is not None:
        host_info = get_host(host, session_key)

        if host_info is not None:

            if mac_address is None:
                mac_address = host_info.get('mac_address', None)

            if ip_address is None:
                ip_address = host_info.get('ip_address', None)

            if port is None:
                port = host_info.get('port', None)

    # Make sure we have a MAC address to perform a request on, stop if we don't
    if mac_address is None:
        raise ValueError("No MAC address was provided and unable to resolve one from the hosts table")

    # Do the wake-on-LAN request
    result = {}

    if logger is not None:
        logger.info("Wake-on-LAN running against host with MAC address=%s", mac_address)

    # Make the kwargs
    keyword_args = {}

    if port is not None and port != '':
        keyword_args['port'] = port

    # Only add the IP address if a port was provided. See https://lukemurphey.net/issues/1733.
    if port in keyword_args and ip_address is not None and ip_address != '':
        keyword_args['ip_address'] = ip_address

    if logger is not None:
        logger.debug("Arguments provided to wake-on-lan: %r", keyword_args)

    # Make the call
    wol.send_magic_packet(mac_address, **keyword_args)

    # Make a dictionary that indicates what happened
    result['message'] = "Wake-on-LAN request successfully sent"
    result['mac_address'] = mac_address

    # Add in the arguments
    result.update(keyword_args)

    # Write the event as a stash new file
    if index is not None:
        writer = StashNewWriter(index=index, source_name=source, sourcetype=sourcetype,
                                file_extension=".stash_output")

        # Log that we performed the wake-on-lan request
        if logger:
            logger.debug("Wrote stash file=%s", writer.write_event(result))

    return result

def whois(host, index=None, sourcetype="whois", source="whois_search_command", logger=None):
    """
    Performs a whois request. If the host is a domain-name then a normal DNS whois will be
    performed. If the name is an IP address, then an IP whois will be done.
    """

    # See if this is an IP address. If so, do an IP whois.
    try:
        # The following will throw a ValueError exception indicating that this is not an IP address
        IPAddress(host)

        whois_object = IPWhois(host)
        results_orig = whois_object.lookup_rdap(depth=1)
    except ValueError:

        # Since this isn't an IP address, run a domain whois
        results_orig = get_whois(host)

    if 'query' not in results_orig:
        results_orig['query'] = host

    result = flatten(results_orig, ignore_blanks=True)

    # Pull out raw so that we can put it at the end. This is done in case the raw field contains
    # things that might mess up the extractions.
    raw = result.get('raw', None)

    try:
        del result['raw']
        result['raw'] = raw
    except KeyError:
        pass # Ok, raw didn't exist

    # Write the event as a stash new file
    if index is not None:
        writer = StashNewWriter(index=index, source_name=source, sourcetype=sourcetype,
                                file_extension=".stash_output")

        # Log that we performed the whois request
        if logger:
            logger.debug("Wrote stash file=%s", writer.write_event(result))

    return result

def nslookup(host, server=None, index=None, sourcetype="nslookup",
             source="nslookup_search_command", logger=None):
    """
    Perform a DNS lookup. If the input is an IP address, then a reverse lookup will be performed.
    """

    result = collections.OrderedDict()

    if host is None or host.strip() == "":
        raise ValueError("The host cannot be none or empty")

    # Add the hostname we are querying for
    result['query'] = host

    # See if this is an IP address. If so, do a reverse lookup.
    try:
        IPAddress(host)

        addr = reversename.from_address(host)

        if len(resolver.query(addr, "PTR")) > 0:
            result['host'] = str(resolver.query(addr, "PTR")[0])

    # If this isn't an IP address, handle it as a DNS name.
    except ValueError:
        # Make a resolver
        custom_resolver = resolver.Resolver()

        if server is not None:
            custom_resolver.nameservers = [server]

        # Log the server used
        result['server'] = custom_resolver.nameservers

        # NS records
        try:
            answers = custom_resolver.query(host, 'NS')

            ns_records = []

            for answer in answers:
                ns_records.append(str(answer))

            if len(ns_records) > 0:
                result['ns'] = ns_records

        except resolver.NoAnswer:
            pass

        # A
        try:
            answers = custom_resolver.query(host, 'A')

            a_records = []

            for answer in answers:
                a_records.append(str(answer))

            if len(a_records) > 0:
                result['a'] = a_records
        except resolver.NoAnswer:
            pass

        # AAAA
        try:
            answers = custom_resolver.query(host, 'AAAA')

            aaaa_records = []

            for answer in answers:
                aaaa_records.append(str(answer))

            if len(aaaa_records) > 0:
                result['aaaa'] = aaaa_records

        except resolver.NoAnswer:
            pass

        # MX
        try:
            answers = custom_resolver.query(host, 'MX')

            mx_records = []

            for answer in answers:
                mx_records.append(str(answer))

            if len(mx_records) > 0:
                result['mx'] = mx_records

        except resolver.NoAnswer:
            pass

    # Write the event as a stash new file
    if index is not None:
        writer = StashNewWriter(index=index, source_name=source, sourcetype=sourcetype,
                                file_extension=".stash_output")

        # Log the data
        if logger:
            logger.debug("Wrote stash file=%s", writer.write_event(result))

    return result

def portscan(host, ports="22,80,443,3389", index=None, sourcetype="portscan", source="portscan_search_command", logger=None, timeout=5):
    """
    Perform a port scan against the given host
    """
    results = port_scan(host, ports, timeout=timeout)

    # Write the event as a stash new file
    if index is not None:
        writer = StashNewWriter(index=index, source_name=source, sourcetype=sourcetype,
                                file_extension=".stash_output")

        # Log that we performed the scan
        for result in results:
            if logger:
                logger.debug("Wrote stash file=%s", writer.write_event(result))
            else:
                writer.write_event(result)

    return results