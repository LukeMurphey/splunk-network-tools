# Copyright (C) 2017 Luke Murphey. All Rights Reserved.
#
# This file contains all possible options for an network_tools.conf file.  Use this file to  
# configure how the network_tools app functions.
#
# To learn more about configuration files (including precedence) please see the documentation 
# located at http://docs.splunk.com/Documentation/latest/Admin/Aboutconfigurationfiles

#****************************************************************************** 
# These options must be set under an [default] entry to apply to all inputs
# Otherwise, the stanza name must be associated with the individual input.
#****************************************************************************** 
index = <string>
    * Defines the default index where results will go that are created by the various search commands
    * Examples: main, networktools

thread_limit = <string>
    * Defines the maximum number of the threads that the input will run when doing pings via the ping input
    * Raising this will increase the number of inputs that can be done at any one time
    * Lower this value if you experience excesssive resource utilization upon startup due to the inputs trying to catch up
    * Raise this value if you have a large number of inputs and Splunk is unable to keep up
    * Defaults to 20