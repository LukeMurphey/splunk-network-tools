import logging
import cherrypy

import splunk.appserver.mrsparkle.controllers as controllers
from splunk.appserver.mrsparkle.lib import jsonresponse
from splunk.appserver.mrsparkle.lib.util import make_splunkhome_path
from splunk.appserver.mrsparkle.lib.decorators import expose_page

from network_tools_app import wakeonlan, ping

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

    @expose_page(must_login=True, methods=['GET', 'POST'])
    def ping(self, host):
        result = {}

        try:
            output, return_code, data = ping(host, source="network_tools_controller", logger=logger)

            result = {
                'success': True,
                'output' : output,
                'return_code': return_code
            }

            result.update(data)

        except Exception as e:
            result = {
                'success': False,
                'message': str(e)
            }

            logger.exception("Wake-on-lan request failed")

        return self.render_json(result)

    @expose_page(must_login=True, methods=['GET', 'POST'])
    def wake(self, host):

        try:
            result = wakeonlan(host, index="main", source="network_tools_controller", logger=logger)

            desc = {
                'success': True
            }

            desc.update(result)

        except Exception as e:
            desc = {
                'success': False,
                'message': str(e)
            }

        return self.render_json(desc)
        