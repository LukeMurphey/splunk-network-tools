import logging
import os
import sys
import json
import cherrypy
import re
import base64

from splunk import AuthorizationFailed, ResourceNotFound
import splunk.appserver.mrsparkle.controllers as controllers
import splunk.appserver.mrsparkle.lib.util as util
from splunk.appserver.mrsparkle.lib import jsonresponse
from splunk.appserver.mrsparkle.lib.util import make_splunkhome_path
import splunk.clilib.bundle_paths as bundle_paths
from splunk.util import normalizeBoolean as normBool
from splunk.appserver.mrsparkle.lib.decorators import expose_page
from splunk.appserver.mrsparkle.lib.routes import route
import splunk.entity as entity
from splunk.rest import simpleRequest

def setup_logger(level):
    """
    Setup a logger for the REST handler.
    """

    logger = logging.getLogger('splunk.appserver.network_tools.controllers.NetworkToolsHelper')
    logger.propagate = False # Prevent the log messages from being duplicated in the python.log file
    logger.setLevel(level)

    file_handler = logging.handlers.RotatingFileHandler(make_splunkhome_path(['var', 'log', 'splunk', 'network_tools_helper_controller.log']), maxBytes=25000000, backupCount=5)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

logger = setup_logger(logging.DEBUG)

class NetworkToolsHelper(controllers.BaseController):
    '''
    A controller for providing backend helper functions for the Network Toolkit app.
    '''
 
    DEFAULT_NAMESPACE ="network_tools"
    DEFAULT_OWNER = "nobody"
    
    def render_error_json(self, msg):
        output = jsonresponse.JsonResponse()
        output.data = []
        output.success = False
        output.addError(msg)
        cherrypy.response.status = 400
        return self.render_json(output, set_mime='text/plain')
 
    def ping(self, host):
        pass
        