"""
This module provides a wrapper around the ping module but adds the ability to scan network ranges.
"""
import os
import re
import zipimport

from . import ping, tcp_ping

# This will import the ipaddress library from the modular input library
# Note that the normal import from a zip file didn't work for me on all platforms (Windows and
# Linux) since it wouldn't import sub-modules (like modular_input.contrib). Thus, I had to rely on
# the zipimport method instead. See https://lukemurphey.net/issues/2173
path_to_mod_input_lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../modular_input.zip')
importer = zipimport.zipimporter(path_to_mod_input_lib)
modular_input = importer.load_module('modular_input')
ipaddress = modular_input.contrib.ipaddress

DOMAIN_NAME_RE = re.compile('^((?!-))(xn--)?[a-z0-9][a-z0-9-_]{0,61}[a-z0-9]{0,1}\.(xn--)?([a-z0-9\-]{1,61}|[a-z0-9-]{1,30}\.[a-z]{2,})$')


class NetworkDestinationTooHigh(Exception):
    """The number of hosts to scan is excessively high."""

def ping_all(dest, count=1, index=None, sourcetype="ping", source="ping_search_command", logger=None, callback=None):
    """
    Pings the host using the native ping command on the platform and returns a tuple consisting of:

     1) the output string
     2) the return code (0 is the expected return code)
     3) parsed output from the ping command
    """
    results = []

    # Convert the entry to unicode since this is what the ipaddress library expects 
    dest = unicode(dest)

    # Try to treat this as an IP address by default
    try:
        # Parse the ipaddress if necessary
        dest_network = ipaddress.ip_network(dest, strict=False)

        if logger:
            logger.debug("Resolved destination to addresses; dest=%s, address_count=%i", dest, dest_network.num_addresses)

        if dest_network.num_addresses == 1:
            _, return_code, result = ping(str(dest_network.network_address), count, index=index, logger=logger)

            result['return_code'] = return_code

            # Make sure that the destination is present
            if 'dest' not in result:
                result['dest'] = str(dest)

            if callback:
                callback(result)

            results.append(result)
        elif dest_network.num_addresses >= 1024:
            raise NetworkDestinationTooHigh("The number of addresses to ping must be less than 1025 but the count requested was %s" % dest_network.num_addresses)
        else:
            for next_dest in dest_network.hosts():
                _, return_code, result = ping(str(next_dest), count, index=index, logger=logger)
                result['return_code'] = return_code

                # Make sure that the destination is present
                if 'dest' not in result:
                    result['dest'] = str(dest)

                if callback:
                    callback(result)

                results.append(result)
    except ValueError:
        # Otherwise, treat this as a domain if it appears to be a domain name
        _, return_code, result = ping(str(dest), count, sourcetype=sourcetype, source=source, index=index, logger=logger)

        result['return_code'] = return_code

        # Make sure that the destination is present
        if 'dest' not in result:
            result['dest'] = str(dest)

        if callback:
            callback(result)

        results.append(result)

    return results

def tcp_ping_all(dest, port, count=1, index=None, sourcetype="ping", source="ping_search_command", logger=None, callback=None):
    """
    Pings the host using the native ping command on the platform and returns a tuple consisting of:

     1) the output string
     2) the return code (0 is the expected return code)
     3) parsed output from the ping command
    """
    results = []

    # Convert the entry to unicode since this is what the ipaddress library expects 
    dest = unicode(dest)

    # Try to treat this as an IP address by default
    try:
        # Parse the ipaddress if necessary
        dest_network = ipaddress.ip_network(dest, strict=False)

        if dest_network.num_addresses == 1:
            result = tcp_ping(str(dest_network.network_address), port, count, index=index, logger=logger)

            if callback:
                callback(result)

            results.append(result)
        elif dest_network.num_addresses >= 100:
            raise Exception("The number of addresses to ping must be less than 100 but the count requested was %s" % dest_network.num_addresses)
        else:
            for next_dest in dest_network.hosts():
                result = tcp_ping(str(next_dest), port, count, index=index, logger=logger)

                if callback:
                    callback(result)

                results.append(result)
    except ValueError:
        # Otherwise, treat this as a domain if it appears to be a domain name
        result = tcp_ping(str(dest), port, count, sourcetype=sourcetype, source=source, index=index, logger=logger)

        if callback:
            callback(result)

        results.append(result)

    return results