from network_tools_app.search_command import SearchCommand
from network_tools_app import nslookup

class NSLookup(SearchCommand):
    
    def __init__(self, host=None, server=None):
        SearchCommand.__init__(self, run_in_preview=False, logger_name="nslookup_search_command")
        
        self.host = host
        self.server = server
        
        self.logger.info("NSLookup running against host=%s", host)
    
    def handle_results(self, results, in_preview, session_key):
        
        # FYI: we ignore results since this is a generating command
        
        # Do the nslookup
        result = nslookup(host=self.host, server=self.server, index="main", logger=self.logger)
        
        self.logger.info("%r", result)
        
        # Output the results
        self.output_results([result])
        
if __name__ == '__main__':
    NSLookup.execute()