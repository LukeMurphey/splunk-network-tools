"""
This module provides a Splunk search command that runs a whois.
"""

from network_tools_app.search_command import SearchCommand
from network_tools_app import whois, get_default_index
from network_tools_app.flatten import dict_to_table

class Whois(SearchCommand):
    """
    A search command for performing whois lookups.
    """

    def __init__(self, host=None):
        SearchCommand.__init__(self, run_in_preview=False, logger_name="whois_search_command")

        self.host = host

        self.logger.info("Whois running against host=%s", host)

    def handle_results(self, results, session_key, in_preview):

        # FYI: we ignore results since this is a generating command

        # Do the whois
        index = get_default_index(session_key)

        results = whois(host=self.host, index=index, logger=self.logger)

        # Convert the output to a series of rows for better output in the search output
        processed = dict_to_table(results)

        # Sort the items
        processed = sorted(processed, key=lambda e: e['attribute'])

        # Output the results
        self.output_results(processed)

if __name__ == '__main__':
    Whois.execute()
