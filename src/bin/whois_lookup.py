"""
This is a search command for doing whois lookups on results.
"""

import logging

from network_tools_app import whois
from network_tools_app.custom_lookup import CustomLookup

class WhoisLookup(CustomLookup):
    """
    This class implements the functionality necessary to make a custom search command.
    """

    def __init__(self):
        """
        Constructs an instance of the whois lookup command.
        """

        # Here is a list of the accepted fieldnames
        fieldnames = ['raw', 'updated_date', 'nameservers', 'registrar', 'whois_server', 'query', 
                      'creation_date', 'emails', 'expiration_date', 'status', 'id', 'asn',
                      'asn_cidr', 'asn_country_code', 'asn_date', 'asn_registry', 'network.cidr',
                      'network.end_address', 'network.ip_version', 'network.handle',
                      'network.links', 'network.name', 'network.parent_handle',
                      'network.start_address', 'query', 'emails', 'expiration_date',
                      'creation_date']
        CustomLookup.__init__(self, fieldnames, 'whois_lookup_command', logging.INFO)

    def do_lookup(self, host):
        """
        Perform a whois lookup against the given host.
        """

        self.logger.info("Running whois against host=%s", host)
        output = whois(host=host, index=None)
        return output

WhoisLookup.main()
