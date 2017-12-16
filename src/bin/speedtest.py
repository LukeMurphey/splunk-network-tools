import os
import sys

path_to_mod_input_lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modular_input.zip')
sys.path.insert(0, path_to_mod_input_lib)
from modular_input import Field, ModularInput, IntegerField

from network_tools_app import speedtest, get_default_index

class SpeedtestInput(ModularInput):
    def __init__(self, timeout=30):

        scheme_args = {'title': "Internet Connection Speedtest",
                       'description': "A speedtest of the Internet connection",
                       'use_single_instance': False}

        args = [
            Field("server", "Server", "The server to use for testing; will be automatically assigned if left blank", empty_allowed=True, none_allowed=True, required_on_create=False, required_on_edit=False),
            IntegerField("runs", "Runs", "The number of runs that should be executed", empty_allowed=False, none_allowed=False)
        ]

        ModularInput.__init__(self, scheme_args, args, logger_name='speedtest_modular_input')

    def run(self, stanza, cleaned_params, input_config):

        #interval = cleaned_params["interval"]
        host = cleaned_params.get("host", None)
        index = cleaned_params.get("index", "default")
        sourcetype = cleaned_params.get("sourcetype", "speedtest")

        server = cleaned_params.get("server", None)
        runs = cleaned_params.get("runs", 3)

        self.logger.info("Starting speedtest, stanza=%s", stanza)
        result = speedtest(host=server, runs=runs, index=index, logger=self.logger)

        # Output the results
        self.output_event(result, stanza, index, sourcetype, stanza, host)

        self.logger.info("Speedtest complete, stanza=%s", stanza)

if __name__ == '__main__':

    speedtest_input = None

    try:
        speedtest_input = SpeedtestInput()
        speedtest_input.execute()
        sys.exit(0)
    except Exception as exception:

        # This logs general exceptions that would have been unhandled otherwise (such as coding
        # errors)
        if speedtest_input is not None and speedtest_input.logger is not None:
            speedtest_input.logger.exception("Unhandled exception was caught, this may be due to a defect in the script")
        else:
            raise exception
