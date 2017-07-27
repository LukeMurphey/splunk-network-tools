"""
This is a search command for doing traceroute lookups on results.
"""

import logging

from network_tools_app import traceroute
from network_tools_app.custom_lookup import CustomLookup

class TracerouteLookup(CustomLookup):
    """
    This class implements the functionality necessary to make a custom search command.
    """

    def __init__(self):
        """
        Constructs an instance of the traceroute lookup command.
        """

        # Here is a list of the accepted fieldnames
        fieldnames = ['return_code', 'raw_output', 'hops']
        CustomLookup.__init__(self, fieldnames, 'traceroute_lookup_command', logging.INFO)

    def do_lookup(self, host):
        """
        Perform a traceroute lookup against the given host.
        """

        self.logger.info("Running traceroute against host=%s", host)
        raw_output, return_code, output = traceroute(host=host, index=None)

        # Flatten the input into a dictionary
        converted_output = {}
        converted_output['return_code'] = return_code
        converted_output['raw_output'] = raw_output

        #Get info on each hop and make it into a field
        hop_strings = []
        for hop in output:
            
            hop_str = hop['ip'][0]

            if hop['ip'][0] != hop['name'][0]:
                hop_str += "(" + hop['name'][0] + ")"

            hop_strings.append(hop_str)

        converted_output['hops'] = ", ".join(hop_strings)

        return converted_output

TracerouteLookup.main()
