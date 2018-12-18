"""
This is a search command for doing ping lookups on results.
"""

import logging


from network_tools_app import ping
from network_tools_app.custom_lookup import CustomLookup

class PingLookup(CustomLookup):
    """
    This class implements the functionality necessary to make a custom search command.
    """

    def __init__(self):
        """
        Constructs an instance of the ping lookup command.
        """

        # Here is a list of the accepted fieldnames
        fieldnames = ['sent', 'received', 'packet_loss', 'min_ping', 'max_ping', 'avg_ping',
                      'jitter', 'return_code', 'raw_output']
        CustomLookup.__init__(self, fieldnames, 'ping_lookup_command', logging.INFO)

    def do_lookup(self, host):
        """
        Perform a ping against the given host.
        """

        self.logger.info("Running ping against host=%s", host)
        raw_output, return_code, output = ping(host=host, index=None)

        output['return_code'] = return_code
        output['raw_output'] = raw_output
        return output

PingLookup.main()
