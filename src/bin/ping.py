"""
This script provides a modular input for performing pings.
"""
import sys

from network_tools_app.modular_input import ModularInput, IntegerField, DurationField, ListField

from network_tools_app import ping

class PingInput(ModularInput):
    """
    This is the class that provides the ping functionality for pinging.
    """

    def __init__(self):

        scheme_args = {'title': "Ping a Host",
                       'description': "Ping a host to see if it responds",
                       'use_single_instance': True}

        args = [
            #Field("title", "Title", "A short description (typically just the domain name)", empty_allowed=False),
            ListField("hosts", "Hosts", "The list of hosts to ping", empty_allowed=True, none_allowed=True, required_on_create=False, required_on_edit=False),
            IntegerField("runs", "Runs", "The number of runs that should be executed", empty_allowed=False, none_allowed=False),
            DurationField("interval", "Interval", "The interval defining how often to perform the check; can include time units (e.g. 15m for 15 minutes, 8h for 8 hours)", empty_allowed=False)
        ]

        ModularInput.__init__(self, scheme_args, args, logger_name='ping_modular_input')

    def run(self, stanza, cleaned_params, input_config):

        #interval = cleaned_params["interval"]
        host = cleaned_params.get("host", None)
        index = cleaned_params.get("index", "default")
        sourcetype = cleaned_params.get("sourcetype", "ping_input")

        hosts = cleaned_params.get("hosts", [])
        runs = cleaned_params.get("runs", 3)

        self.logger.info("Starting ping, stanza=%s", stanza)

        for host in hosts:
            output, return_code, result = ping(host=host, count=runs, logger=self.logger)

            # Output the results
            self.output_event(result, stanza, index, sourcetype, stanza, host)

        self.logger.info("Ping complete, stanza=%s", stanza)

if __name__ == '__main__':

    ping_input = None

    try:
        ping_input = PingInput()
        ping_input.execute()
        sys.exit(0)
    except Exception as e:

        # This logs general exceptions that would have been unhandled otherwise (such as coding
        # errors)
        if ping_input is not None and ping_input.logger is not None:
            ping_input.logger.exception("Unhandled exception was caught, this may be due to a defect in the script")
        else:
            raise e
