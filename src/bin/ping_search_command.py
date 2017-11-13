"""
This module provides a Splunk search command that runs and parse the output of the ping command.
"""
import os
import sys

from network_tools_app.search_command import SearchCommand
from network_tools_app import ping, get_default_index

path_to_mod_input_lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modular_input.zip')
sys.path.insert(0, path_to_mod_input_lib)
from modular_input.contrib import ipaddress

class Ping(SearchCommand):
    """
    This search command provides a Splunk interface for the system's ping command.
    """

    def __init__(self, dest=None, count=1, index=None):
        SearchCommand.__init__(self, run_in_preview=False, logger_name="ping_search_command")

        self.dest = unicode(dest)
        self.index = index

        try:
            self.count = int(count)
        except ValueError:
            raise ValueError('The count parameter must be an integer')

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

        # Parse the ipaddress if necessary
        dest = ipaddress.ip_network(self.dest, strict=False)

        results = []

        # Do the ping
        if dest.num_addresses == 1:
            _, return_code, result = ping(str(dest.network_address), self.count, index=index, logger=self.logger)

            result['return_code'] = return_code
            results.append(result)
        elif dest.num_addresses >= 100:
            raise Exception("The number of addresses to ping must be less than 100 but the count requested was %s" % dest.num_addresses)
        else:
            for next_dest in dest.hosts():
                _, return_code, result = ping(str(next_dest), self.count, index=index, logger=self.logger)
                result['return_code'] = return_code
                results.append(result)

        # Output the results
        self.output_results(results)

if __name__ == '__main__':
    Ping.execute()
