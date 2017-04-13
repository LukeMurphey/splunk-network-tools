"""
This module provides a Splunk search command that runs and parse the output of the ping command.
"""

from network_tools_app.search_command import SearchCommand
from network_tools_app import ping, get_default_index

class Ping(SearchCommand):
    """
    This search command provides a Splunk interface for the system's ping command.
    """

    def __init__(self, host=None, count=1):
        SearchCommand.__init__(self, run_in_preview=False, logger_name="ping_search_command")

        self.host = host

        try:
            self.count = int(count)
        except ValueError:
            raise ValueError('The count parameter must be an integer')

        self.logger.info("Ping running")

    def handle_results(self, results, session_key, in_preview):

        # FYI: we ignore results since this is a generating command

        # Do the ping
        index = get_default_index(session_key)

        _, return_code, result = ping(self.host, self.count, index=index, logger=self.logger)

        result['return_code'] = return_code

        # Output the results
        self.output_results([result])

if __name__ == '__main__':
    Ping.execute()
