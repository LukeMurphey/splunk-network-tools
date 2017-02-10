from network_tools_app.search_command import SearchCommand
from network_tools_app import whois
from network_tools_app.flatten import dict_to_table

class Whois(SearchCommand):
    
    def __init__(self, host=None):
        SearchCommand.__init__(self, run_in_preview=False, logger_name="whois_search_command")
        
        self.host = host
        
        self.logger.info("Whois running against host=%s", host)
    
    def handle_results(self, results, in_preview, session_key):
        
        # FYI: we ignore results since this is a generating command
        
        # Do the whois
        results = whois(host=self.host, index="main", logger=self.logger)
        
        # Convert the output to a series of rows for better output in the search output
        processed = dict_to_table(results)
        
        # Sort the items
        processed = sorted(processed, key=lambda e: e['attribute'])
        
        """
        processed.append({
            'attribute' : 'raw',
            'value' : raw
        })
        """
        
        # Output the results
        self.output_results(processed)
        
if __name__ == '__main__':
    Whois.execute()