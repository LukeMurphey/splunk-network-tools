import os
import re
import sys

from . import ping

path_to_mod_input_lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../modular_input.zip')
sys.path.insert(0, path_to_mod_input_lib)
from modular_input.contrib import ipaddress

DOMAIN_NAME_RE = re.compile('^((?!-))(xn--)?[a-z0-9][a-z0-9-_]{0,61}[a-z0-9]{0,1}\.(xn--)?([a-z0-9\-]{1,61}|[a-z0-9-]{1,30}\.[a-z]{2,})$')

def ping_all(dest, count=1, index=None, sourcetype="ping", source="ping_search_command", logger=None, callback=None):
    """
    Pings the host using the native ping command on the platform and returns a tuple consisting of:

     1) the output string
     2) the return code (0 is the expected return code)
     3) parsed output from the ping command
    """
    results = []

    # Convert the entry to unicode since 
    dest = unicode(dest)

    # Treat this as a domain if it appears to be a domain name
    if DOMAIN_NAME_RE.match(dest):
        _, return_code, result = ping(str(dest), count, sourcetype=sourcetype, source=source, index=index, logger=logger)

        result['return_code'] = return_code

        if callback:
            callback(result)

        results.append(result)

    # Treat this as an IP address otherwise
    else:
        # Parse the ipaddress if necessary
        dest_network = ipaddress.ip_network(dest, strict=False)

        if dest_network.num_addresses == 1:
            _, return_code, result = ping(str(dest_network.network_address), count, index=index, logger=logger)

            result['return_code'] = return_code

            if callback:
                callback(result)

            results.append(result)
        elif dest_network.num_addresses >= 100:
            raise Exception("The number of addresses to ping must be less than 100 but the count requested was %s" % dest_network.num_addresses)
        else:
            for next_dest in dest_network.hosts():
                _, return_code, result = ping(str(next_dest), count, index=index, logger=logger)
                result['return_code'] = return_code

                if callback:
                    callback(result)

                results.append(result)

    return results
