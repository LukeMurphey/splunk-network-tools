"""
This module provides a Splunk search command that runs a whois.
"""

from network_tools_app.search_command import SearchCommand
from network_tools_app import whois, get_default_index
from network_tools_app.flatten import dict_to_table

class Whois(SearchCommand):
    """
    A search command for performing whois lookups.
    """

    def __init__(self, host=None, field=None):
        SearchCommand.__init__(self, run_in_preview=False, logger_name="whois_search_command")

        self.host = host

        if host is not None:
            self.logger.info("Whois running against host=%s", host)

        self.field = field

    def handle_results(self, results, session_key, in_preview):

        # Get the index to output to
        index = get_default_index(session_key)

        # Make sure that the host field was provided
        if self.host is None:
            self.logger.warn("No host was provided")
            return

        if results is None or len(results) == 0:
            # FYI: we ignore results since this is a generating command

            # Do the whois
            output = whois(host=self.host, index=index, logger=self.logger)

            # Convert the output to a series of rows for better output in the search output
            processed = dict_to_table(output)

            # Sort the items
            processed = sorted(processed, key=lambda e: e['attribute'])

            # Output the results
            self.output_results(processed)
        
        else:
            
            # Make a cache to store previously looked up results
            cache = {}

            for result in results:
                
                # Process each result
                if self.field in result:
                    
                    host_to_lookup = result[self.field]

                    # See if we looked up the host already
                    if host_to_lookup in cache:
                        output = cache[host_to_lookup]

                    # Otherwise, pull the host from the cache
                    else:
                        output = whois(host=host_to_lookup, index=index, logger=self.logger)
                        cache[host_to_lookup] = output

                    # Add the output
                    result.update(output)

            # Output the results
            self.output_results(results)

if __name__ == '__main__':
    Whois.execute()
