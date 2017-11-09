"""
This provides a search command for waking hosts via WoL protocol.
"""

import sys

from network_tools_app.search_command import SearchCommand
from network_tools_app import wakeonlan

class WakeOnLAN(SearchCommand):
    """
    A search command for performing WoL requests.
    """

    def __init__(self, host=None, mac_address=None, ip_address=None, port=None):
        SearchCommand.__init__(self, run_in_preview=False, logger_name="wakeonlan_search_command")

        self.mac_address = None
        self.ip_address = None
        self.port = None

        # Get the port (if provided)
        try:

            if port is not None:
                self.port = int(port)

        except ValueError:
            sys.stderr.write('The port parameter must be an integer')
            return

        # Get the IP address (if provided)
        if ip_address is not None:
            self.ip_address = ip_address

        # Get the MAC address (if provided)
        if mac_address is not None:
            self.mac_address = mac_address

        # Get the host to lookup address
        self.host = host

    def handle_results(self, results, session_key, in_preview):

        # FYI: we ignore results since this is a generating command

        # Do the wake-on-LAN
        try:
            result = wakeonlan(self.host, mac_address=self.mac_address, ip_address=self.ip_address,
                               port=self.port, session_key=session_key, logger=self.logger)
        except Exception as exception:
            self.logger.exception("Exception generated when attempting to perform wake-on-LAN request")
            raise exception

        # Output the results
        self.output_results([result])

if __name__ == '__main__':
    WakeOnLAN.execute()
