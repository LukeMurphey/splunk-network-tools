"""
This script provides a modular input for performing port scans.
"""
import os
import sys
import threading
import time
import json
import logging

import splunk

path_to_mod_input_lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modular_input.zip')
sys.path.insert(0, path_to_mod_input_lib)
from modular_input import ModularInput, DurationField, IPNetworkField, DomainNameField, Field, ListField, MultiValidatorField
from modular_input.shortcuts import forgive_splunkd_outages

from network_tools_app import portscan
from network_tools_app.parseintset import parseIntSet

if sys.version_info.major >= 3:
    unicode = str

class DomainOrIPNetworkField(MultiValidatorField):
    def __init__(self, name, title, description, none_allowed=False, empty_allowed=True,
                 required_on_create=None, required_on_edit=None):
        super(DomainOrIPNetworkField, self).__init__(name, title, description, none_allowed, empty_allowed, required_on_create, required_on_edit, validators=[DomainNameField, IPNetworkField])

class PortRangeField(Field):
    def to_python(self, value, session_key=None):
        Field.to_python(self, value, session_key)

        if value is None:
            return None

        try:
            ports_list = parseIntSet(value, True)
        except ValueError:
            raise FieldValidationException("The value of '%s' for the '%s' parameter is not a valid list" % (str(value), self.name))

        return ports_list

    def to_string(self, value):

        if value is None or len(value) == 0:
            return ""

        if isinstance(value, (str, unicode)):
            return value
        
        elif isinstance(value, list):
            value_strings = [str(i) for i in value]
            return ",".join(value_strings)

        return ",".join(value)

class PortScanInput(ModularInput):
    """
    This is the class that provides the ping functionality for port scanning.
    """

    DEFAULT_THREAD_LIMIT = 200

    # This stores the default app config information
    default_app_config = None

    def __init__(self, thread_limit=None):

        scheme_args = {'title': "Port Scan",
                       'description': "Port scan a host to see what ports are open",
                       'use_single_instance': True}

        args = [
            ListField("dest", "Destination", "The list of hosts or networks to port scan", empty_allowed=True, none_allowed=True, required_on_create=True, required_on_edit=True, instance_class=DomainOrIPNetworkField),
            PortRangeField("ports", "Ports", "The TCP ports to scan", empty_allowed=False, none_allowed=False, required_on_create=True, required_on_edit=True),
            DurationField("interval", "Interval", "The interval defining how often to perform the check; can include time units (e.g. 15m for 15 minutes, 8h for 8 hours)", empty_allowed=False)
        ]

        ModularInput.__init__(self, scheme_args, args, logger_name='portscan_modular_input', logger_level=logging.DEBUG)

        if thread_limit is None:
            self.thread_limit = PortScanInput.DEFAULT_THREAD_LIMIT
        else:
            self.thread_limit = thread_limit

        self.threads = {}

    @forgive_splunkd_outages
    def get_app_config(self, session_key, stanza="default"):
        """
        Get the app configuration.

        Arguments:
        session_key -- The session key to use when connecting to the REST API
        stanza -- The stanza to get the app information from (defaults to "default")
        """

        # If the stanza is empty, then just use the default
        if stanza is None or stanza.strip() == "":
            stanza = "default"

        network_tools_config = None

        # Get the app configuration
        try:
            uri = '/servicesNS/nobody/-/admin/network_tools/' + stanza

            getargs = {
                'output_mode': 'json'
            }

            _, entry = splunk.rest.simpleRequest(uri, sessionKey=session_key, getargs=getargs,
                                                 raiseAllErrors=True)

            network_tools_config = json.loads(entry)['entry'][0]['content']

            # Convert the thread limit to an integer
            if 'thread_limit' in network_tools_config:
                network_tools_config['thread_limit'] = int(network_tools_config['thread_limit'])

            self.logger.debug("App config information loaded, stanza=%s", stanza)

        except splunk.ResourceNotFound:
            self.logger.error('Unable to find the app configuration for the specified configuration stanza=%s, error="not found"', stanza)
            raise
        except splunk.SplunkdConnectionException:
            self.logger.error('Unable to find the app configuration for the specified configuration stanza=%s error="splunkd connection error", see url=http://lukemurphey.net/projects/splunk-website-monitoring/wiki/Troubleshooting', stanza)
            raise

        return network_tools_config

    def run(self, stanza, cleaned_params, input_config):

        interval = cleaned_params["interval"]
        host = cleaned_params.get("host", None)
        index = cleaned_params.get("index", "default")
        sourcetype = cleaned_params.get("sourcetype", "portscan_input")
        source = cleaned_params.get("source", stanza)

        dests = cleaned_params.get("dest", [])
        ports = cleaned_params.get("ports", None)

        # Load the thread_limit if necessary
        # This should only be necessary once in the processes lifetime
        if self.default_app_config is None:

            # Get the default app config
            self.default_app_config = self.get_app_config(input_config.session_key)

            # Get the limit from the app config
            loaded_thread_limit = self.default_app_config['thread_limit']

            # Ensure that the thread limit is valid
            if loaded_thread_limit is not None and loaded_thread_limit > 0:
                self.thread_limit = loaded_thread_limit
                self.logger.debug("Thread limit successfully loaded, thread_limit=%r",
                                  loaded_thread_limit)

            # Warn that the thread limit is invalid
            else:
                self.logger.warn("The thread limit is invalid and will be ignored, thread_limit=%r", loaded_thread_limit)

        # Determines if the input needs another run
        elif self.needs_another_run(input_config.checkpoint_dir, stanza, interval):

            self.logger.debug("Starting portscan, stanza=%s", stanza)

            # Get the time that the input last ran
            last_ran = self.last_ran(input_config.checkpoint_dir, stanza)
            for dest in dests:
                results = portscan(dest, ports, index, sourcetype, source, self.logger)

                self.logger.debug("Successfully port scanned the host=%s, ports=%s", str(dest), str(ports))

            # Save the checkpoint so that we remember when we last ran the input
            self.save_checkpoint_data(input_config.checkpoint_dir, stanza,
                                        {
                                            'last_run' : self.get_non_deviated_last_run(last_ran, interval, stanza)
                                        })

            self.logger.debug("Port scan complete, stanza=%s", stanza)

if __name__ == '__main__':
    PortScanInput.instantiate_and_execute()
