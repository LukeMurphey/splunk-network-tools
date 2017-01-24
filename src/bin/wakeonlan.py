from network_tools_app.search_command import SearchCommand
from network_tools_app.wakeonlan import wol

import splunk.rest as rest

import json
import sys

class WakeOnLAN(SearchCommand):
    
    def __init__(self, host=None, mac_address=None, ip_address=None, port=None):
        SearchCommand.__init__(self, run_in_preview=True, logger_name="wakeonlan_search_command")
        
        self.params = {}
        self.mac_address = None
        
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
            
        # Get the MAC address (if provided)
        if mac_address is not None:
            self.mac_address = mac_address
            
        # Get the host to lookup address  
        self.host = host
        
    def getHost(self, name, session_key):
        
        uri = '/servicesNS/nobody/network_tools/storage/collections/data/network_hosts'
        
        getargs = {
            'output_mode': 'json',
            'query' : '{"name":"' + name + '"}'
        }
        
        _, l = rest.simpleRequest(uri, sessionKey=session_key, getargs=getargs, raiseAllErrors=True)
        l  = json.loads(l)
    
        # Make sure we got at least one result
        if len(l) > 0:
            self.logger.info("Successfully found an entry in the table of hosts for host=%s", name)
            return l[0]
        
        else:
            self.logger.warn("Failed to find an entry in the table of hosts for host=%s", name)
            return None
    
    def handle_results(self, results, session_key, in_preview):
        
        # FYI: we ignore results since this is a generating command
        
        # Resolve the MAC address (and port and IP address) if needed
        host_info = None
        
        if self.host is not None:
            host_info = self.getHost(self.host, session_key)
            
            if host_info is not None:
                
                if self.mac_address is None:
                    self.mac_address = host_info['mac_address']
                
                if 'ip_address' not in self.params and host_info.get('ip_address', None) is not None and len(host_info['ip_address']) > 0:
                    self.params['ip_address'] = host_info['ip_address']
                    
                if 'port' not in self.params and host_info.get('port', None) is not None and len(host_info['port']) > 0:
                    self.params['port'] = host_info['port']
                
        
        # Make sure we have a MAC address to perform a request on, stop if we don't
        if self.mac_address is None:
            raise ValueError("No MAC address was provided and unable to resolve one from the hosts table")
            return
        
        # Do the wake-on-LAN request
        result = {}
        
        self.logger.info("Wake-on-LAN running against host with MAC address=%s", self.mac_address)
        wol.send_magic_packet(self.mac_address, **self.params)
        
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