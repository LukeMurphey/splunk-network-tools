#!/usr/bin/env python
# coding: utf-8
"""
Parses the output of the system ping command.
"""
__version__ = '0.4'

from optparse import OptionGroup, OptionParser

import re
import sys
import collections

from compat import text_type

__all__ = ["parse",
           "format_ping_result",
           "main",
           ]

class PingParseException(Exception):
    pass

# Pull regex compilation out of parser() so it only gets done once

# Parse first line of output containing the domain
host_matcher = re.compile(r'ping(?:ing)? ([a-zA-Z0-9.\-]+)', re.IGNORECASE)

# Old version, failed on OS X due to 0.0% formatted percentage (November 20, 2016, ssteinerX)
# https://regex101.com/r/zt9G2w/1
# rslt_matcher = re.compile(r'(\d+) packets transmitted, '
#                            '(\d+) (?:packets )?received,'
#                            ' (\d+)% packet loss')

# This one works on OS X output which includes the percentage in 0.0% format
# https://regex101.com/r/nmjQzI/2
rslt_matcher = re.compile(r'(?P<sent>\d+) packets transmitted, (?P<received>\d+) (?:packets )?received, (?P<packet_loss>\d+\.?\d*)% packet loss')
rslt_matcher_windows = re.compile(r'Sent = (?P<sent>\d+), Received = (?P<received>\d+), Lost = \d+ \((?P<packet_loss>\d+\.?\d*)% loss')
#rslt_matcher_windows = re.compile(r'.*')


# Pull out round-trip min/avg/max/stddev = 49.042/49.042/49.042/0.000 ms
# TODO: make this more specific i.e. match a bit before the '=' sign
minmax_matcher = re.compile(r'(?P<min>\d+.\d+)/(?P<avg>\d+.\d+)/(?P<max>\d+.\d+)/(?P<jitter>\d+.\d+)')
minmax_matcher_windows = re.compile(r'Minimum = (?P<min>\d+.?\d*)ms, Maximum = (?P<max>\d+.?\d*)ms, Average = (?P<avg>\d+.?\d*)ms')

# Available replacements
format_replacements = [('%h', 'host'),
                       ('%s', 'sent'),
                       ('%r', 'received'),
                       ('%p', 'packet_loss'),
                       ('%m', 'minping'),
                       ('%a', 'avgping'),
                       ('%M', 'maxping'),
                       ('%j', 'jitter')]

# Default output just prints fields in `format_replacements` order
default_format = ','.join([fmt for fmt, field in format_replacements])


def _get_match_groups(ping_output, regex, names=None, msg=""):
    """
    Get groups by matching regex in output from ping command.
    """
    
    # Try each regex if multiple are provided
    if isinstance(regex, (list, tuple)):
        
        for r in regex:
            
            try:
                return _get_match_groups(ping_output, r, names)
            except PingParseException:
                continue # Try the next one
            
        # We got no matches
        raise PingParseException('Invalid PING output:\n' + ping_output)
        
    match = regex.search(ping_output)
    
    if not match:
        raise PingParseException('Invalid PING output:\n' + ping_output)
    
    # Extract the named fields
    if names is not None:
        out = []
        
        for name in names:
            
            try:
                out.append(match.group(name))
            except IndexError:
                # Couldn't find this field, till it with None
                out.append(None)
            
        return out
    
    return match.groups()


def parse(ping_output):
    """
    Parse `ping_output` string into a dictionary containing the following
    fields:

        `host`: *string*; the target hostname that was pinged
        `sent`: *int*; the number of ping request packets sent
        `received`: *int*; the number of ping reply packets received
        `packet_loss`: *int*; the percentage of  packet loss
        `minping`: *float*; the minimum (fastest) round trip ping request/reply
                    time in milliseconds
        `avgping`: *float*; the average round trip ping time in milliseconds
        `maxping`: *float*; the maximum (slowest) round trip ping time in
                    milliseconds
        `jitter`: *float*; the standard deviation between round trip ping times
                    in milliseconds
    """

    if not isinstance(ping_output, text_type):
        ping_output = text_type(ping_output)

    host = _get_match_groups(ping_output, host_matcher)[0]
    sent, received, packet_loss = _get_match_groups(ping_output, [rslt_matcher, rslt_matcher_windows], ['sent', 'received', 'packet_loss'])

    try:
        minping, avgping, maxping, jitter = _get_match_groups(ping_output,
                                                              [minmax_matcher, minmax_matcher_windows],
                                                              ['min', 'avg', 'max', 'jitter'])
    except PingParseException:
        minping = avgping = maxping = jitter = 'NA'

    d = collections.OrderedDict()
    d['host'] = host
    d['sent'] = sent
    d['received'] = received
    d['packet_loss'] = packet_loss
    d['min_ping'] = minping
    d['avg_ping'] = avgping
    d['max_ping'] = maxping
    d['jitter'] = jitter

    return d


def format_ping_result(ping_result, format_string=default_format):
    """Use format_string to format the ping_result dictionary."""
    output = format_string

    # Get all replacement strings
    replacements = [(fmt, ping_result[field]) for fmt, field in
                    format_replacements]

    # Apply replacements to the output string
    for (fmt, rep) in replacements:
        output = output.replace(fmt, rep)

    return output


def main(argv=sys.argv):

    usage = 'Usage: %prog [OPTIONS] [+FORMAT]\n\n'\
            'Parses output from the system ping command piped in via stdin.'
    parser = OptionParser(usage=usage, version="%prog " + __version__)
    parser.add_option("-i", "--input", dest="filename",
                      help="read input from FILE", metavar="FILE")
    parser.add_option("-f", "--format", dest="format",
                      help="optional format string")
    # NOTE: can't do this as optparse requires 2 character triggers
    # parser.add_option("+", dest="format",
    #                  help="optional format string")

    format_group = OptionGroup(parser,
    """FORMAT controls the output. Interpreted sequences are:
    \t%h    host name or IP address
    \t%s    packets sent
    \t%r    packets received
    \t%p    packet_loss
    \t%m    minimum ping in milliseconds
    \t%a    average ping in milliseconds
    \t%M    maximum ping in milliseconds
    \t%j    jitter in milliseconds

    Default FORMAT is: """ + default_format)

    parser.add_option_group(format_group)
    (options, args) = parser.parse_args()

    ping_output = None

    if options.filename:
        with open(options.filename, 'r') as f:
            ping_output = f.read()
    else:
        # detects whether input is piped in or expected from cmd line
        if not sys.stdin.isatty():
            ping_output = sys.stdin.read()

    if ping_output is None:
        parser.print_help()
        sys.exit(1)

    ping_result = parse(ping_output)

    # NOTE: the "+...format string" will override options.format
    #       if both are there
    format_string = options.format or default_format

    # If there's something left after optparse is done,
    # see if it's a '+' prefixed format string and, if so, use it
    # NOTE: this is from original code and is for compatibility only
    #       use -f format_string instead
    if len(args) >= 1:
        if args[0].startswith('+'):
            args[0] = args[0].lstrip('+')
            format_string = ' '.join(args[0:])
        else:
            parser.print_help()
            sys.exit(1)

    output = format_ping_result(ping_result, format_string)
    sys.stdout.write(output)

    sys.exit(0)

if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        pass