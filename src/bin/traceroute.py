"""
The Traceroute search command allows a user to run a traceroute and view the output.

The results will be indexed for later viewing if the user so wishes to see the results again.
"""

from network_tools_app.search_command import SearchCommand
from network_tools_app import traceroute

from splunk.util import normalizeBoolean

class Traceroute(SearchCommand):
    """
    This class is the interface between the search command and the underlying traceroute module.
    """

    def __init__(self, host=None, include_output=False):
        SearchCommand.__init__(self, run_in_preview=True, logger_name="traceroute_search_command")

        self.host = host
        self.include_output = normalizeBoolean(include_output)

        self.logger.info("Traceroute running")

    def handle_results(self, results, in_preview, session_key):

        # FYI: we ignore results since this is a generating command

        # Do the traceroute
        _, return_code, result = traceroute(self.host, index="main", logger=self.logger, include_raw_output=self.include_output)

        #result['return_code'] = return_code

        # Output the results
        self.output_results(result)

if __name__ == '__main__':
    Traceroute.execute()
