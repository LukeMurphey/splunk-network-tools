"""
This class is a helper that will perform a bandwidth speedtest, prepare the results for viewing in Splunk, and indexing the event.
"""
from event_writer import StashNewWriter
import pyspeedtest


def do_speedtest(host, runs=2, index=None, sourcetype="speedtest", source="speedtest_search_command", logger=None):
    
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
    
    # Log that we performed the ping
    if logger:
        logger.info("Wrote stash file=%s", writer.write_event(result))
        
    # Return the result
    return result
    