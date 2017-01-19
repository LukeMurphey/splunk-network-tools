from network_tools_app.search_command import SearchCommand
from network_tools_app.speedtest_helper import do_speedtest

class Speedtest(SearchCommand):
    
    def __init__(self, runs=1, host=None):
        SearchCommand.__init__(self, run_in_preview=True, logger_name="speedtest_search_command")
        
        self.host = host
        
        try:
            self.runs = int(runs)
        except ValueError:
            raise ValueError('The runs parameter must be an integer')
        
        self.logger.info("Speedtest running")
    
    def handle_results(self, results, in_preview, session_key):
        
        # FYI: we ignore results since this is a generating command
        
        # Do the speedtest
        result = do_speedtest(host=self.host, runs=self.runs, index="main", logger=self.logger)
        
        # Output the results
        self.output_results([result])
        
if __name__ == '__main__':
    Speedtest.execute()