from network_tools_app.search_command import SearchCommand
from network_tools_app import pyspeedtest

class Speedtest(SearchCommand):
    
    def __init__(self, runs=1):
        SearchCommand.__init__(self, run_in_preview=True, logger_name="speedtest")
        
        self.params = {
            'runs' : runs
        }
        
        self.logger.info("Speedtest running")
    
    def handle_results(self, results, in_preview, session_key):
        
        # FYI: we ignore results since this is a generating command
        
        # Do the speedtest
        result = {}
        
        st = pyspeedtest.SpeedTest(**self.params)
        result['ping'] = st.ping()
        result['download'] = st.download()
        result['upload'] = st.upload()
        result['server'] = st.host
        
        # Output the results
        self.output_results([result])
        
if __name__ == '__main__':
    Speedtest.execute()