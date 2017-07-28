"""
This is a search command for doing nslookups on results.
"""

import logging

from network_tools_app import nslookup
from network_tools_app.custom_lookup import CustomLookup

class NSLookup(CustomLookup):
    """
    This class implements the functionality necessary to make a custom search command.
    """

    def __init__(self):
        """
        Constructs an instance of the NSlookup command.
        """

        # Here is a list of the accepted fieldnames
        fieldnames = ['a', 'aaaa', 'query', 'mx', 'ns', 'server', 'hostname']
        CustomLookup.__init__(self, fieldnames, 'nslookup_lookup_command', logging.DEBUG)

    def do_lookup(self, host):
        """
        Perform an nslookup lookup against the given host.
        """

        self.logger.info("Running nslookup against host=%s", host)
        output = dict(nslookup(host=host, index=None))

        if 'host' in output:
            output['hostname'] = output['host']
            del output['host']

        return output

NSLookup.main()
