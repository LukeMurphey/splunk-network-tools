from network_tools_app.search_command import SearchCommand
from network_tools_app import pyspeedtest

class Speedtest(SearchCommand):
    
    def __init__(self, runs=1, server=None):
        SearchCommand.__init__(self, run_in_preview=True, logger_name="speedtest")
        
        self.params = {
                'host' : server
        }
        
        try:
            self.params['runs'] = int(runs)
        except ValueError:
            raise ValueError('The runs parameter must be an integer')
        
        self.logger.info("Speedtest running")
    
    def handle_results(self, results, in_preview, session_key):
        
        # FYI: we ignore results since this is a generating command
        
        # Do the speedtest
        result = {}
        
        st = pyspeedtest.SpeedTest(**self.params)
        result['ping'] = round(st.ping(),2)
        result['download'] = round(st.download(),2)
        result['download_readable'] = pyspeedtest.pretty_speed(st.download())
        
        result['upload'] = round(st.upload(),2)
        result['upload_readable'] = pyspeedtest.pretty_speed(st.upload())
        
        result['server'] = st.host
        
        # Output the results
        self.output_results([result])
        
if __name__ == '__main__':
    Speedtest.execute()