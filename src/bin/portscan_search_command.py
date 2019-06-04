"""
This module provides a Splunk search command that performs port scans.
"""
import os
import re
import sys

from network_tools_app.search_command import SearchCommand
from network_tools_app import get_default_index
from network_tools_app import portscan
from network_tools_app.parseintset import parseIntSet

class PortScan(SearchCommand):
    """
    This search command provides a Splunk interface for performing port scans.
    """

    def __init__(self, dest=None, ports=None, index=None, host=None, timeout=5):
        SearchCommand.__init__(self, run_in_preview=False, logger_name="portscan_search_command")

        self.dest = dest

        # Use the host argument if someone provided that instead (since that is the older argument supported by some of the other commands)
        if self.dest is None and host is not None:
            self.dest = host

        self.index = index

        if ports is None:
            raise ValueError('The list of ports to scan must be provided')

        try:
            parseIntSet(ports, True)
        except ValueError:
            raise ValueError('The list of ports to scan is invalid')

        self.ports = ports

        try:
            self.timeout = int(timeout)
        except ValueError:
            raise ValueError('The must be a valid integer')

        if self.timeout <= 0:
            raise ValueError('The must be a valid positive integer (greater than zero)')

        self.logger.info("Port scan running")

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

        # Do the port scan
        results = portscan(self.dest, self.ports, index=index, timeout=self.timeout)

        self.logger.info("Port scan complete")

        # Output the results
        self.output_results(results)

if __name__ == '__main__':
    PortScan.execute()
