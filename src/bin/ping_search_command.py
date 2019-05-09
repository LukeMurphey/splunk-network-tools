"""
This module provides a Splunk search command that runs and parse the output of the ping command.
"""
import os
import re
import sys

from network_tools_app.search_command import SearchCommand
from network_tools_app import get_default_index
from network_tools_app.ping_network import ping_all, tcp_ping_all

class Ping(SearchCommand):
    """
    This search command provides a Splunk interface for the system's ping command.
    """

    def __init__(self, dest=None, count=1, port=None, index=None, host=None):
        SearchCommand.__init__(self, run_in_preview=False, logger_name="ping_search_command")

        self.dest = None

        if dest is not None:
            self.dest = unicode(dest)

        # Use the host argument if someone provided that instead (since that is the old argument)
        elif self.dest is None and host is not None:
            self.dest = unicode(host)

        self.index = index

        try:
            self.count = int(count)
        except ValueError:
            raise ValueError('The count parameter must be an integer')

        if port is not None:
            try:
                self.port = int(port)
            except ValueError:
                raise ValueError('The port parameter must be an integer')

            if self.port < 1 or self.port > 65535:
                raise ValueError('The port parameter must be an integer from 1 to 65535')

        else:
            self.port = None

        self.logger.info("Ping running")

    def handle_results(self, results, session_key, in_preview):

        # FYI: we ignore results since this is a generating command

        # Make sure that the dest field was provided
        if self.dest is None:
            self.logger.warn("No dest was provided")
            return

        # Get the index
        if self.index is not None:
            index = self.index
        else:
            index = get_default_index(session_key)

        # Do the ping
        if self.port is None:
            results = ping_all(self.dest, self.count, index=index, logger=self.logger)
        else:
            results = tcp_ping_all(self.dest, self.port, self.count, index=index, logger=self.logger)

        # Output the results
        self.output_results(results)

if __name__ == '__main__':
    Ping.execute()
