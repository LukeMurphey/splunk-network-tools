# App provided imports
from event_writer import StashNewWriter
import pyspeedtest
import pingparser
from tracerouteparser import TracerouteParser 

# Environment imports
from platform import system as system_name
import subprocess
import collections
import os
import binascii

def traceroute(host, unique_id=None, index=None, sourcetype="traceroute", source="traceroute_search_command", logger=None, include_dest_info=True):
    """
    Performs a traceroute using the the native traceroute command and returns the output in a parsed format.
    """
    
    cmd = ["traceroute"]
    
    # Add the host argument
    cmd.append(host)
    
    # Run the traceroute command and get the output
    output = None
    return_code = None
    
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return_code = 0
    except subprocess.CalledProcessError as e:
        output = e.output
        return_code = e.returncode
        
    # Parse the output
    try:
        trp = TracerouteParser()
        trp.parse_data(output)
        
        # This will contain the hops
        parsed = []
        
        hop_idx = 0
        
        # Make an entry for each hop
        for h in trp.hops:
            
            if h.probes is None or len(h.probes) == 0:
                continue
            
            hop_idx = hop_idx + 1
            
            # This will track the probes
            rtts = []
            ips = []
            names = []
            
            hop = collections.OrderedDict()
            hop['hop'] = hop_idx
            
            for probe in h.probes:
                
                if probe.rtt is not None:
                    rtts.append(str(probe.rtt))
                
                if probe.ipaddr is not None:
                    ips.append(probe.ipaddr)
                                    
                if probe.name is not None:
                    names.append(probe.name)
            
            hop['rtt'] = rtts
            hop['ip'] = ips
            hop['name'] = names
            
            if include_dest_info:
                hop['dest_ip'] = trp.dest_ip
                hop['dest_host'] = trp.dest_name
            
            parsed.append(hop)
            
    except Exception as e:
        raise Exception("Unable to parse traceroute output")
        
    # Write the event as a stash new file
    if index is not None:
        writer = StashNewWriter(index=index, source_name=source, sourcetype=sourcetype, file_extension=".stash_output")
        
        # Let's store the basic information for the traceroute that will be included with each hop
        proto = collections.OrderedDict()
        
        # Include the destination info if it was included already
        if not include_dest_info:
            proto['dest_ip'] = trp.dest_ip
            proto['dest_host'] = trp.dest_name
        
        if unique_id is None:
            unique_id = binascii.b2a_hex(os.urandom(4))
            
        proto['unique_id'] = unique_id
        
        for r in parsed:
            
            result = collections.OrderedDict()
            result.update(r)
            result.update(proto)
            
            # Log that we performed the traceroute
            if logger:
                logger.info("Wrote stash file=%s", writer.write_event(result))
            
            #results.append(result)
    

            
    return output, return_code, parsed

def ping(host, count=1, index=None, sourcetype="ping", source="ping_search_command", logger=None):
    """
    Pings the host using the native ping command on the platform and returns a tuple consisting of: the output string and the return code (0 is the expected return code).
    """
    
    cmd = ["ping"]
    
    # Add the argument of the number of pings
    if system_name().lower=="windows":
        cmd.extend(["-n", str(count)])
    else:
        cmd.extend(["-c", str(count)])
    
    # Add the host argument
    cmd.append(host)
    
    output = None
    return_code = None
    
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return_code = 0
    except subprocess.CalledProcessError as e:
        output = e.output
        return_code = e.returncode
    
    # Parse the output
    try:
        parsed = pingparser.parse(output)
    except Exception:
        parsed = {}
    
    # Write the event as a stash new file
    if index is not None:
        writer = StashNewWriter(index=index, source_name=source, sourcetype=sourcetype, file_extension=".stash_output")
        
        result = collections.OrderedDict()
        result.update(parsed)
        
        result['dest'] = result['host']
        del result['host']
        result['return_code'] = return_code
        result['output'] = output
    
        # Log that we performed the ping
        if logger:
            logger.info("Wrote stash file=%s", writer.write_event(result))
            
    return output, return_code, parsed

def speedtest(host, runs=2, index=None, sourcetype="speedtest", source="speedtest_search_command", logger=None):
    """
    Performs a bandwidth speedtest and sends the results to an index.
    """
    # This will contain the event we will index and return
    result = {}
        
    st = pyspeedtest.SpeedTest(host=host, runs=runs)
    result['ping'] = round(st.ping(),2)
    
    result['download'] = round(st.download(),2)
    result['download_readable'] = pyspeedtest.pretty_speed(st.download())
        
    result['upload'] = round(st.upload(),2)
    result['upload_readable'] = pyspeedtest.pretty_speed(st.upload())
        
    result['server'] = st.host
    
    # Write the event as a stash new file
    if index is not None:
        writer = StashNewWriter(index=index, source_name=source, sourcetype=sourcetype, file_extension=".stash_output")
    
        # Log that we performed the speedtest
        if logger:
            logger.info("Wrote stash file=%s", writer.write_event(result))
        
    # Return the result
    return result
    

