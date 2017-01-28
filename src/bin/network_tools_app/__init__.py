from event_writer import StashNewWriter
import pyspeedtest
import pingparser
from platform import system as system_name
import subprocess
import collections

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
    

