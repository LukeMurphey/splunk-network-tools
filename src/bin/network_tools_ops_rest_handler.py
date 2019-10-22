"""
This REST handler provides helper methods to the front-end views that need to perform various network operations.
"""

import logging
import csv
import time

from splunk.appserver.mrsparkle.lib.util import make_splunkhome_path
from splunk import AuthorizationFailed, ResourceNotFound

# The default of the csv module is 128KB; upping to 10MB. See SPL-12117 for
# the background on issues surrounding field sizes.
# (this method is new in python 2.5)
csv.field_size_limit(10485760)

def setup_logger(level):
    """
    Setup a logger for the REST handler
    """

    logger = logging.getLogger('splunk.appserver.network_tools_ops_rest_handler.rest_handler')
    logger.propagate = False # Prevent the log messages from being duplicated in the python.log file
    logger.setLevel(level)

    log_file_path = make_splunkhome_path(['var', 'log', 'splunk', 'network_tools_ops_rest_handler.log'])
    file_handler = logging.handlers.RotatingFileHandler(log_file_path, maxBytes=25000000,
                                                        backupCount=5)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

logger = setup_logger(logging.DEBUG)

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from network_tools_app import rest_handler
from network_tools_app import ping, whois, nslookup, traceroute, wakeonlan

class NetworkOperationsHandler(rest_handler.RESTHandler):
    """
    This is a REST handler that supports:

     1) Pings
     2) Traceroutes
     3) Whois requests
     4) Wake-on-LAN requests 
    """

    def __init__(self, command_line, command_arg):
        super(NetworkOperationsHandler, self).__init__(command_line, command_arg, logger)

    def get_ping(self, request_info, host=None, **kwargs):
        """
        Perform a ping.
        """

        if host is None:
            return self.render_error_json("Unable to perform network operation: no host argument provided")

        result = {}

        try:
            output, return_code, data = ping(host, source="network_tools_controller", logger=logger)
               
            result = {
                'success': True,
                'output' : output,
                'return_code': return_code
            }

            # Add the data we got
            result.update(data)

            # Everything worked, return accordingly
            return {
                'payload': result, # Payload of the request.
                'status': 200 # HTTP status code
            }

        except:
            self.logger.exception("Exception generated when attempting to perform an operation")
            return self.render_error_json("Unable to perform network operation")

    def get_whois(self, request_info, host=None, **kwargs):
        """
        Perform a whois.
        """

        if host is None:
            return self.render_error_json("Unable to perform network operation: no host argument provided")

        try:
            output = whois(host, source="network_tools_controller", logger=logger)

            # Everything worked, return accordingly
            return {
                'payload': output, # Payload of the request.
                'status': 200 # HTTP status code
            }

        except:
            self.logger.exception("Exception generated when attempting to perform an operation")
            return self.render_error_json("Unable to perform network operation")

    def get_nslookup(self, request_info, host=None, **kwargs):
        """
        Perform a nslookup.
        """

        if host is None:
            return self.render_error_json("Unable to perform network operation: no host argument provided")

        try:
            output = nslookup(host, source="network_tools_controller", logger=logger)

            # Everything worked, return accordingly
            return {
                'payload': output, # Payload of the request.
                'status': 200 # HTTP status code
            }

        except:
            self.logger.exception("Exception generated when attempting to perform an operation")
            return self.render_error_json("Unable to perform network operation")

    def get_traceroute(self, request_info, host=None, **kwargs):
        """
        Perform a traceroute.
        """

        if host is None:
            return self.render_error_json("Unable to perform network operation: no host argument provided")

        try:
            output = traceroute(host, source="network_tools_controller", logger=logger)

            # Everything worked, return accordingly
            return {
                'payload': output, # Payload of the request.
                'status': 200 # HTTP status code
            }

        except:
            self.logger.exception("Exception generated when attempting to perform an operation")
            return self.render_error_json("Unable to perform network operation")

    def post_wake(self, request_info, host=None, **kwargs):
        """
        Perform a wake-on-LAN request.
        """

        if host is None:
            return self.render_error_json("Unable to perform network operation: no host argument provided")

        try:
            output = wakeonlan(host, source="network_tools_controller", logger=logger, session_key=request_info.session_key)

            # Everything worked, return accordingly
            return {
                'payload': output, # Payload of the request.
                'status': 200 # HTTP status code
            }

        except:
            self.logger.exception("Exception generated when attempting to perform an operation")
            return self.render_error_json("Unable to perform network operation")
