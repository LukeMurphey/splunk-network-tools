from network_tools_app.search_command import SearchCommand
from network_tools_app import speedtest, get_default_index

class Speedtest(SearchCommand):
    """
    A Search command for performing a speedtest.
    """

    def __init__(self, runs=1, server=None):
        SearchCommand.__init__(self, run_in_preview=False, logger_name="speedtest_search_command")

        self.server = server

        try:
            self.runs = int(runs)
        except ValueError:
            raise ValueError('The runs parameter must be an integer')

        self.logger.info("Speedtest running")

    def handle_results(self, results, session_key, in_preview):

        # FYI: we ignore results since this is a generating command

        # Do the speedtest
        index = get_default_index(session_key)

        result = speedtest(host=self.server, runs=self.runs, index=index, logger=self.logger)

        # Output the results
        self.output_results([result])

if __name__ == '__main__':
    Speedtest.execute()
