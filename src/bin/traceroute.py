from network_tools_app.search_command import SearchCommand
from network_tools_app import traceroute

class Traceroute(SearchCommand):
    
    def __init__(self, host=None, count=1):
        SearchCommand.__init__(self, run_in_preview=True, logger_name="traceroute_search_command")
        
        self.host = host
        
        self.logger.info("Traceroute running")
    
    def handle_results(self, results, in_preview, session_key):
        
        # FYI: we ignore results since this is a generating command
        
        # Do the traceroute
        _, return_code, result = traceroute(self.host, index="main", logger=self.logger)
        
        #result['return_code'] = return_code
        
        # Output the results
        self.output_results(result)
        
if __name__ == '__main__':
    Traceroute.execute()