"""
This is a search command for doing port scan lookups on results.
"""

import logging

from network_tools_app import portscan
from network_tools_app.custom_lookup import CustomLookup

class PortScanLookup(CustomLookup):
    """
    This class implements the functionality necessary to make a custom search command.
    """

    def __init__(self):
        """
        Constructs an instance of the ping lookup command.
        """

        # Here is a list of the accepted fieldnames
        fieldnames = ['dest', 'ports', 'closed_ports', 'open_ports']
        CustomLookup.__init__(self, fieldnames, 'portscan_lookup_command', logging.INFO)

    def do_lookup(self, host, ports=None):
        """
        Perform a portscan against the given host.
        """

        self.logger.info("Running port scan against host=%s", host)

        # Use a default for the ports
        if ports is None or len(ports) == 0:
            # From https://securitytrails.com/blog/top-scanned-ports
            ports = "21,22,23,25,53,80,110,111,135,139,143,443,445,993,995,1723,3306,3389,5900,8080"
    
        data = {
            'dest': host,
            'ports': ports,
            'closed_ports': [],
            'open_ports': []
        }

        results = portscan(host, ports)

        # Convert the results
        for result in results:
            data['dest'] = result['dest']

            # Add the port to the necessary list
            if result['status'] == 'open':
                data['open_ports'].append(result['port'])
            else:
                data['closed_ports'].append(result['port'])

        self.logger.info("data=%r", data)

        return data

PortScanLookup.main()
