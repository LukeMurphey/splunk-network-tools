"""
This defines a REST handler for front-ending the network_tools.conf file.
"""

from network_tools_app.simple_rest_handler import RestHandler, IntegerFieldValidator, BooleanFieldValidator
import logging
import splunk.admin as admin

class NetworkToolsRestHandler(RestHandler):
    """
    A REST handler for the network_tools.conf file.
    """

    # Below is the name of the conf file (example.conf)
    conf_file = 'network_tools'

    # Below are the list of parameters that are accepted
    PARAM_INDEX = 'index'

    # Below are the list of valid and required parameters
    valid_params = [PARAM_INDEX]
    required_params = []

    # List of fields and how they will be validated
    field_validators = {}

    # General variables
    app_name = "network_tools"

    # Logger info
    logger_file_name = 'network_tools_rest_handler.log'
    logger_name = 'NetworkToolsRestHandler'
    logger_level = logging.INFO

# initialize the handler
if __name__ == "__main__":
    admin.init(NetworkToolsRestHandler, admin.CONTEXT_NONE)
