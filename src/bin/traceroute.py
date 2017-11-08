"""
The Traceroute search command allows a user to run a traceroute and view the output.

The results will be indexed for later viewing if the user so wishes to see the results again.
"""

from network_tools_app.search_command import SearchCommand
from network_tools_app import traceroute, get_default_index

from splunk.util import normalizeBoolean

class Traceroute(SearchCommand):
    """
    This class is the interface between the search command and the underlying traceroute module.
    """

    def __init__(self, host=None, include_output=False, index=None):
        SearchCommand.__init__(self, run_in_preview=False, logger_name="traceroute_search_command")

        self.host = host
        self.include_output = normalizeBoolean(include_output)
        self.index = index

        self.logger.info("Traceroute running")

    def handle_results(self, results, session_key, in_preview):

        # FYI: we ignore results since this is a generating command

        # Make sure that the host field was provided
        if self.host is None:
            self.logger.warn("No host was provided")
            return

        # Get the index
        if self.index is not None:
            index = self.index
        else:
            index = get_default_index(session_key)

        # Do the traceroute
        _, return_code, result = traceroute(self.host, index=index, logger=self.logger, include_raw_output=self.include_output)

        #result['return_code'] = return_code

        # Output the results
        self.output_results(result)

if __name__ == '__main__':
    Traceroute.execute()
