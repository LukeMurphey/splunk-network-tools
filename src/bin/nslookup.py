"""
This module provides a Splunk search command that performs a DNS lookup.
"""

from network_tools_app.search_command import SearchCommand
from network_tools_app import nslookup, get_default_index

class NSLookup(SearchCommand):
    """
    This search command provides a Splunk interface for doing a DNS lookup.
    """

    def __init__(self, host=None, server=None):
        SearchCommand.__init__(self, run_in_preview=False, logger_name="nslookup_search_command")

        self.host = host
        self.server = server

        self.logger.info("NSLookup running against host=%s", host)

    def handle_results(self, results, session_key, in_preview):

        # FYI: we ignore results since this is a generating command

        # Make sure that the host field was provided
        if self.host is None:
            self.logger.warn("No host was provided")
            return

        # Do the nslookup
        index = get_default_index(session_key)

        result = nslookup(host=self.host, server=self.server, index=index, logger=self.logger)

        # Output the results
        self.output_results([result])

if __name__ == '__main__':
    NSLookup.execute()
