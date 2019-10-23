"""
This class implements a class for parsing traceroute output.
"""

import re
from compat import text_type

class Probe(object):
    """
    This represents a traceroute probe. A probe is one attempt to get info from one hop.
    """
    def __init__(self, rtt, dest, dest_ip):

        self.dest = None
        self.rtt = None
        self.dest_ip = None

        # Process the RTT
        if rtt is not None and len(rtt) > 0 and rtt[0] == '<':
            self.rtt = int(rtt[1:])
        elif rtt == '*' or rtt is None:
            self.rtt = None
        elif len(rtt) > 0:
            self.rtt = float(rtt)

        # Process the dest
        if dest == 'Request timed out.':
            self.dest = None
        elif dest is not None:
            self.dest = dest.strip()

        # Process the dest_ip
        if dest_ip == 'Request timed out.':
            self.dest_ip = None
        elif dest_ip is not None:
            self.dest_ip = dest_ip.strip()

class Hop(object):
    """
    This represents a single hop between a host and its destination.
    A hop can contain multiple probes (since a single hop may be tested more than once).
    """
    def __init__(self, number=None):
        self.number = number
        self.probes = []

    def add_probe(self, probe):
        """
        Add a probe to this hop.
        """

        if probe is not None:

            # Populate the dest from the previous probe if it doesn't have it defined
            if probe.dest is None and len(self.probes) > 0:
                probe.dest = self.probes[-1].dest

            # Populate the dest_ip from the previous probe if it doesn't have it defined
            if probe.dest_ip is None and len(self.probes) > 0:
                probe.dest_ip = self.probes[-1].dest_ip

            # Add the probe
            self.probes.append(probe)

class UnexpectedInputException(Exception):
    """
    This exception is generated when input was observed that is unexpected.
    """

    pass

class Traceroute(object):
    """
    This class will parse traceroutes done using the command-line tools like "traceroute" and
    "tracert".
    """

    # Regexs for things to disregard
    TRACE_COMPLETE = re.compile(r'^\s*Trace complete')
    HOP_COUNT = re.compile(r'^\s*over a maximum of .* hops')
    TRACEROUTE_WARNING = re.compile(r'^\s*traceroute: Warning:')
    EMPTY_LINES = re.compile(r'^\s*$')
    IGNORE_LIST = [TRACE_COMPLETE, EMPTY_LINES, TRACEROUTE_WARNING, HOP_COUNT]

    # Regexs for parsing the headers
    HEADER_RE_WINDOWS = re.compile(r'^Tracing route to (?P<dest>\S+) (\[(?P<dest_ip>\d+\.\d+\.\d+\.\d+)\])?')
    HEADER_RE_NIX = re.compile(r'traceroute to (?P<dest>\S+) \((?P<dest_ip>\d+\.\d+\.\d+\.\d+)\)')
    HEADER_RE_LIST = [HEADER_RE_WINDOWS, HEADER_RE_NIX]

    # Regexs for parsing the probes

    # https://regex101.com/r/Ip5pMY
    HOP_RE_WINDOWS = re.compile(r'^\s*(?P<hop>\d+)\s+(?P<probe_1><?[\d*]*)(\s*ms)?\s+(?P<probe_2><?[\d*]*)(\s*ms)?\s*(?P<probe_3><?[\d*]*)(\s*ms)?\s*(?P<dest>([^*[ ]+)|(Request timed out[.]))(\s*\[(?P<dest_ip>\d+\.\d+\.\d+\.\d+)\])?\s*$')
    
    # https://regex101.com/r/9HDVV7
    HOP_RE_NIX = re.compile(r'\s*(((?P<hop>\d+)?\s+)?\s+)?((?P<dest>[-.\w]+)\s+)?(\((?P<dest_ip>\d+\.\d+\.\d+\.\d+)\))?\s*(?P<probe_1><?[*0-9]+([.][0-9]+)?)(\s*ms)?(\s+[!]N)?(\s+(?P<probe_2><?[*0-9]+([.][0-9]+)?)(\s*ms))?(\s+[!]N)?(\s+(?P<probe_3><?[*0-9]+([.][0-9]+)?)(\s*ms))?(\s+[!]N)?')
    
    # https://regex101.com/r/QNZXnM/
    HOP_RE_WINDOWS_ERROR_REPORT = re.compile(r'^\s*(?P<hop>\d+)\s+(?P<dest>([^*[ ]+))(\s*\[(?P<dest_ip>\d+\.\d+\.\d+\.\d+)\])?\s*reports[:].*')
    
    HOP_RE_LIST = [HOP_RE_WINDOWS_ERROR_REPORT, HOP_RE_WINDOWS, HOP_RE_NIX]

    def __init__(self):
        self.hops = []

        self.dest = None
        self.dest_ip = None

    @staticmethod
    def parse(output, raise_exception_on_non_matches=False):
        """
        Parse the output and create a traceroute instance from the data.
        """

        # Make the traceroute that we will return once we populate it
        traceroute = Traceroute()

        traceroute.initialize_from_output(output, raise_exception_on_non_matches)

        return traceroute

    def try_to_match(self, line, regexs, find_all=False):
        """
        Try to match the line against the list of regular expressions and return the first that
        matches. If no match is done, return None.
        """

        for regex in regexs:

            # Do a findall if requested
            if find_all:
                matches = []

                for match in regex.finditer(line):
                    matches.append(match)
            else:
                matches = regex.search(line)

            # Return the matches. If we looking for all entries and none matched, return None.
            if find_all and len(matches) > 0:
                return matches
            elif matches:
                return matches

    def try_parse_to_dict(self, line, regexs):
        """
        Try to parse the line with one of the regular expressions and return the dictionary
        from the one that matches first.
        """

        match = self.try_to_match(line, regexs, find_all=False)

        if match:
            return match.groupdict()

    def initialize_from_output(self, output, raise_exception_on_non_matches=False):
        """
        Initialize the class from the given output.
        """

        hop = None

        if not isinstance(output, text_type):
            output = text_type(output)

        # Go through each line
        for line in output.splitlines():

            # See if this is something to just ignore
            if self.try_to_match(line, self.IGNORE_LIST):
                continue

            # Search through the output for the header
            parsed_header = self.try_parse_to_dict(line, self.HEADER_RE_LIST)

            if parsed_header:
                self.dest = parsed_header.get('dest', None)
                self.dest_ip = parsed_header.get('dest_ip', None)

            # Try to parse this as a hop
            else:

                # Parse each hop
                parsed_hops = self.try_to_match(line, self.HOP_RE_LIST, find_all=True)

                if parsed_hops is None:
                    if raise_exception_on_non_matches:
                        raise UnexpectedInputException("Unexpected input was observed: " + line)
                    continue

                for parsed_hop in parsed_hops:

                    parsed_hop = parsed_hop.groupdict()

                    #print parsed_hop

                    if parsed_hop:

                        # Convert the hop number to an integer
                        if parsed_hop.get('hop', None) is not None:
                            hop_number = int(parsed_hop.get('hop', 0))
                        else:
                            hop_number = None

                        hop_dest = parsed_hop.get('dest', None)
                        hop_dest_ip = parsed_hop.get('dest_ip', None)

                        # Copy the dest to dest_ip if it is an IP
                        if hop_dest is not None and hop_dest_ip is None:
                            hop_dest_ip = hop_dest

                        # If there is no hop number, then this a probe for the previous hop.
                        # The lack of a hop number means this probe likely has a different
                        # IP address but is for the same hop. For example, like this:
                        #  8  abc.com (1.2.3.4)  150.90 ms  def.com (1.2.3.5)  62.59 ms
                        if hop is None or hop_number is not None:
                            #print "Making new hop:", hop_number
                            hop = Hop(hop_number)
                            self.hops.append(hop)

                        # Get the probes
                        for i in range(1, 4):

                            rtt = parsed_hop.get('probe_' + str(i), None)

                            if rtt is not None and len(rtt) > 0:
                                #print "Adding probe: ", rtt, hop.number
                                # Make the probe instance
                                probe = Probe(rtt, hop_dest, hop_dest_ip)
                                hop.add_probe(probe)

                        # Add one probe to capture the dest info if this is a new hop but it has no
                        # probes.
                        if (hop_dest is not None or hop_dest_ip is not None) and len(hop.probes) == 0:
                            probe = Probe(None, hop_dest, hop_dest_ip)
                            hop.add_probe(probe)

