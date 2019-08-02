"""
This is a search command for doing whois lookups on results.
"""

import logging

from network_tools_app import whois, get_default_index
from network_tools_app.custom_lookup import CustomLookup
from network_tools_app.dict_translate import translate

class WhoisLookup(CustomLookup):
    """
    This class implements the functionality necessary to make a custom search command.
    """

    TRANSLATION_RULES = [
        # Contact name
        ('objects.*.contact.name', 'contact.name'),

        # Contact email
        ('objects.*.contact.email.*.value', 'contact.email'),

        # Contact phone
        ('objects.*.contact.phone.*.value', 'contact.phone'),

        # Contact address
        ('objects.*.contact.address.*.value', 'contact.address'),
    ]

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

        # Add in the field names from the translation rules
        for rule in self.TRANSLATION_RULES:
            fieldnames.append(rule[1])
    
        CustomLookup.__init__(self, fieldnames, 'whois_lookup_command', logging.INFO)

    def do_lookup(self, host):
        """
        Perform a whois lookup against the given host.
        """

        index = get_default_index()
        self.logger.info("Running whois against host=%s using index=%s", host, index)
        output = whois(host=host, index=index, logger=self.logger)

        return translate(output, self.TRANSLATION_RULES)

WhoisLookup.main()
