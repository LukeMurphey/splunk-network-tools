"""
This script provides a modular input for performing pings.
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
from modular_input import ModularInput, IntegerField, DurationField, ListField, IPNetworkField, DomainNameField, MultiValidatorField, RangeField
from modular_input.shortcuts import forgive_splunkd_outages

from network_tools_app.ping_network import ping_all, tcp_ping_all

class DomainOrIPNetworkField(MultiValidatorField):
   def __init__(self, name, title, description, none_allowed=False, empty_allowed=True,
                 required_on_create=None, required_on_edit=None):
    super(DomainOrIPNetworkField, self).__init__(name, title, description, none_allowed, empty_allowed, required_on_create, required_on_edit, validators=[DomainNameField, IPNetworkField])


class PingInput(ModularInput):
    """
    This is the class that provides the ping functionality for pinging.
    """

    DEFAULT_THREAD_LIMIT = 20

    # This stores the default app config information
    default_app_config = None

    def __init__(self, thread_limit=None):

        scheme_args = {'title': "Ping",
                       'description': "Ping a host or a network to see if it is online",
                       'use_single_instance': True}

        args = [
            ListField("dest", "Destination", "The list of hosts or networks to ping", empty_allowed=True, none_allowed=True, required_on_create=True, required_on_edit=True, instance_class=DomainOrIPNetworkField),
            RangeField("port", "Port", "The TCP port to use (leave blank to use ICMP instead)", low=1, high=65535, empty_allowed=True, none_allowed=True, required_on_create=False, required_on_edit=False),
            RangeField("runs", "Runs", "The number of runs that should be executed", low=1, high=100, empty_allowed=False, none_allowed=False),
            DurationField("interval", "Interval", "The interval defining how often to perform the check; can include time units (e.g. 15m for 15 minutes, 8h for 8 hours)", empty_allowed=False)
        ]

        ModularInput.__init__(self, scheme_args, args, logger_name='ping_modular_input', logger_level=logging.INFO)

        if thread_limit is None:
            self.thread_limit = PingInput.DEFAULT_THREAD_LIMIT
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

    def clean_old_threads(self):
        """
        Remove the old threads that are done.
        """

        # Clean up old threads
        for thread_stanza in list(self.threads.keys()):

            # Keep track of the number of removed threads so that we can make sure to emit a log
            # message noting the number of threads
            removed_threads = 0

            # If the thread isn't alive, prune it
            if not self.threads[thread_stanza].is_alive():
                removed_threads = removed_threads + 1
                self.logger.info("Removing inactive thread for stanza=%s, thread_count=%i", thread_stanza, len(self.threads))
                del self.threads[thread_stanza]

            # If we removed threads, note the updated count in the logs so that it can be tracked
            if removed_threads > 0:
                self.logger.info("Removed inactive threads, thread_count=%i, removed_thread_count=%i", len(self.threads), removed_threads)

    def get_thread_name(self, stanza, host):
        """
        Get the name of the thread that serves as a unique identifier.
        """

        return stanza + ':' + host

    def send_result(self, result, stanza, index, sourcetype, host, source):
        """
        Send the result.
        """

        if 'dest' not in result and 'host' in result:
            result['dest'] = result['host']

        if 'host' in result:
            del result['host']

        with self.lock:
            # Output the results
            self.output_event(result, stanza=stanza, index=index, sourcetype=sourcetype, host=host, source=source)

    def run(self, stanza, cleaned_params, input_config):

        interval = cleaned_params["interval"]
        host = cleaned_params.get("host", None)
        index = cleaned_params.get("index", "default")
        sourcetype = cleaned_params.get("sourcetype", "ping_input")
        source = cleaned_params.get("source", None)

        dests = cleaned_params.get("dest", [])
        runs = cleaned_params.get("runs", 3)
        port = cleaned_params.get("port", None)

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

        # Remove old threads if necessary
        self.clean_old_threads()

        # Stop if we have a running thread
        if stanza in self.threads:
            self.logger.debug("No need to execute this stanza since a thread already running for stanza=%s", stanza)

        # Determines if the input needs another run
        elif self.needs_another_run(input_config.checkpoint_dir, stanza, interval):
            def run_ping():
                self.logger.debug("Starting ping, stanza=%s", stanza)

                # Get the time that the input last ran
                last_ran = self.last_ran(input_config.checkpoint_dir, stanza)
                for dest in dests:
                    try:
                        def output_result_callback(result):
                            """
                            Output the result
                            """
                            self.send_result(result, stanza, index, sourcetype, host, source)

                        if port not in [None, ""]:
                            results = tcp_ping_all(dest, port, count=runs, logger=self.logger, callback=output_result_callback)
                        else:
                            results = ping_all(dest, count=runs, logger=self.logger, callback=output_result_callback)

                        if len(results) == 1:
                            self.logger.debug("Successfully pinged the host=%s", str(dest))
                        elif len(results) > 1:
                            self.logger.info("Successfully pinged all hosts in the network=%s", str(dest))
                    except Exception as e:
                        self.logger.exception(e)

                # Save the checkpoint so that we remember when we last ran the input
                self.save_checkpoint_data(input_config.checkpoint_dir, stanza,
                                          {
                                              'last_run' : self.get_non_deviated_last_run(last_ran, interval, stanza)
                                          })

                self.logger.debug("Ping complete, stanza=%s", stanza)

            # If this is not running in multi-threading mode, then run it now in the main thread
            if self.thread_limit <= 1:
                run_ping()

            # If the number of threads is at or above the limit, then wait until the number of
            # threads comes down
            elif len(self.threads) >= self.thread_limit:
                self.logger.warn("Thread limit has been reached and thus this execution will be skipped for stanza=%s, thread_count=%i", stanza, len(self.threads))

                # Give some time for the inputs to catch up. This prevents spamming the logs with tons
                # of logs as the input tries to check every input even though the threads are maxed out
                time.sleep(1)

            # Execute the input as a separate thread
            else:

                # Start a thread
                new_thread = threading.Thread(name='ping_input:' + stanza, target=run_ping)
                self.threads[stanza] = new_thread
                new_thread.start()

                self.logger.info("Added thread to the queue for stanza=%s, thread_count=%i", stanza, len(self.threads))

if __name__ == '__main__':
    PingInput.instantiate_and_execute()
