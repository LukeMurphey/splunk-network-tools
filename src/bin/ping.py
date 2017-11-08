"""
This module provides a Splunk search command that runs and parse the output of the ping command.
"""

from network_tools_app.search_command import SearchCommand
from network_tools_app import ping, get_default_index

class Ping(SearchCommand):
    """
    This search command provides a Splunk interface for the system's ping command.
    """

    def __init__(self, host=None, count=1, index=None):
        SearchCommand.__init__(self, run_in_preview=False, logger_name="ping_search_command")

        self.host = host
        self.index = index

        try:
            self.count = int(count)
        except ValueError:
            raise ValueError('The count parameter must be an integer')

        self.logger.info("Ping running")

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

        # Do the ping
        _, return_code, result = ping(self.host, self.count, index=index, logger=self.logger)

        result['return_code'] = return_code

        # Output the results
        self.output_results([result])

if __name__ == '__main__':
    Ping.execute()
