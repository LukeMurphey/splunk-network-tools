from network_tools_app.search_command import SearchCommand
from network_tools_app.wakeonlan import wol
import sys

class WakeOnLAN(SearchCommand):
    
    def __init__(self, mac_address, ip_address=None, port=None):
        SearchCommand.__init__(self, run_in_preview=True, logger_name="wakeonlan")
        
        self.params = {}
        
        # Get the port (if provided)
        try:
            
            if port is not None:
                self.params['port'] = int(port)
            
        except ValueError:
            sys.stderr.write('The port parameter must be an integer')
            return
        
        # Get the IP address (if provided)
        if ip_address is not None:
            self.params['ip_address'] = ip_address
          
        # Get the MAC address  
        self.mac_address = mac_address
        
        self.logger.info("Wake-on-LAN running against host with MAC address=%s", mac_address)
    
    def handle_results(self, results, in_preview, session_key):
        
        # FYI: we ignore results since this is a generating command
        
        # Do the wake-on-LAN request
        result = {}
        
        wol.send_magic_packet(self.mac_address) #, **self.params)
        
        result['message'] = "Wake-on-LAN request successfully sent"
        result['mac_address'] = self.mac_address
        
        if 'ip_address' in self.params:
            result['ip_address'] = self.params['ip_address']
        
        if 'port' in self.params:
            result['port'] = self.params['port']
        
        # Output the results
        self.output_results([result])
        
if __name__ == '__main__':
    WakeOnLAN.execute()