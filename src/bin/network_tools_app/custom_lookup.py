"""
This is a base-class for writing custom external lookups.

This is licensed under the Apache License Version 2.0
See https://www.apache.org/licenses/LICENSE-2.0.html

To use this, you will need to:

 1) A lookup command script that implements from CustomLookup
 2) Create a transforms.conf that declares your lookup command
     2.1) The path of your lookup command filename (e.g. echo_lookup.py) and the names of the fields that need to be provided
     2.2) The list of fields that the command will generate (usually will include the field passed into it)


See below for an example. Note that this command can be run with:

* | head 1 | lookup echo host



default/transforms.conf:
--------------------------------

[echo]
external_cmd = echo_lookup.py host
fields_list = host,echohost



bin/echo_lookup.py:
--------------------------------

import logging
from custom_lookup import CustomLookup

class EchoLookup(CustomLookup):
    def __init__(self):
        CustomLookup.__init__(self, ['echohost'], 'echo_lookup_command', logging.INFO)

    def do_lookup(self, host):
        return {'echohost' : host}

EchoLookup.main()
"""

import csv
import sys
import logging
from logging import handlers

from splunk.appserver.mrsparkle.lib.util import make_splunkhome_path

class CustomLookup(object):

    def __init__(self, fieldnames=None, logger_name='custom_lookup_command', log_level=logging.INFO):
        """
        Constructs an instance of the lookup command.

        Arguments:
        fieldnames -- A list of the field names that the command will output
        logger_name -- The logger name to append to the logger
        log_level -- The log level to use for the logger
        """

        # Check and save the logger name
        self._logger = None

        if logger_name is None or len(logger_name) == 0:
            raise Exception("Logger name cannot be empty")

        self.logger_name = logger_name
        self.log_level = log_level

        # Keep a list of the invalid fields so that we don't re-warn people about the same things
        self.invalid_fields = set()

        # Ensure that the list of the accepted fieldnames is valid
        if fieldnames is None or len(fieldnames) == 0:
            raise Exception("The value for fieldnames must include an array of at least one row")

        # Here is a list of the accepted fieldnames
        self.fieldnames = fieldnames

    @property
    def logger(self):
        """
        A property that returns the logger.
        """

        # Make a logger unless it already exists
        if self._logger is not None:
            return self._logger

        logger = logging.getLogger(self.logger_name)

         # Prevent the log messages from being duplicated in the python.log file:
        logger.propagate = False
        logger.setLevel(self.log_level)

        file_handler = handlers.RotatingFileHandler(make_splunkhome_path(['var', 'log', 'splunk', self.logger_name + '.log']), maxBytes=25000000, backupCount=5)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        self._logger = logger
        return self._logger

    @logger.setter
    def logger(self, logger):
        self._logger = logger

    def do_lookup(self, *args, **kwargs):
        """
        This is the function that performs the lookup. It must be sub-classed.
        """
        raise Exception("do_lookup needs to be implemented")

    def extend_fieldnames(self, fieldnames):
        """
        Extends the list of fieldnames with those that the lookup will create.
        """

        fieldnames.extend(self.fieldnames)
        return set(fieldnames)

    def add_result(self, result_dict, output_dict, fieldnames, only_overwrite_empty=False):
        """
        Merge the output into the result dictionary but don't merge in fields that aren't listed in
        fieldnames.
        """

        # Keep a count of the invalid fields so that we can detect if we found new ones
        start_invalid_fields_len = len(self.invalid_fields)

        # Add each field to the output
        for field, value in output_dict.items():

            # Don't overwrite fields with an existing value since this could cause Splunk to not
            # be able to match the results with the original values.
            # see https://lukemurphey.net/issues/2348
            if only_overwrite_empty and result_dict.get(field, 'DOESNT EXIST YET') not in ['', None]:
                self.logger.debug("Skipping blank field %r ", field)
                pass

            # Make sure that field is in the list of field names
            elif field in fieldnames:

                self.logger.debug("Adding field %s with value %r", field, value)

                # If the output is a list, then include a comma deliminated list
                if isinstance(value, (list, tuple)) and not isinstance(value, basestring):
                    result_dict[field] = ", ".join(value)

                # The entry is a flat value, just include it
                else:
                    result_dict[field] = value

            # Detected an unexpected value, log it
            else:
                self.invalid_fields.add(field)

        # Output a warning if there are fields we didn't expect
        if len(self.invalid_fields) > start_invalid_fields_len:
            self.logger.warn("Discovered field that are not in the fields list: %r", self.invalid_fields)

    @classmethod
    def main(cls):
        lookup_command = None

        try:
            lookup_command = cls()
            lookup_command.execute()

        except Exception as e:

            # This logs general exceptions that would have been unhandled otherwise (such as coding
            # errors)
            if lookup_command is not None and lookup_command.logger is not None:
                lookup_command.logger.exception("Unhandled exception was caught, this may be due to a defect in the script")
            else:
                raise e

    def execute(self):
        """
        Execute the lookup command based on the values from standard input and output.
        """

        # This contains a list of the fields to perform an operation on (like "host")
        args = sys.argv[1:]

        # Initialize the input for the results
        infile = sys.stdin
        r = csv.DictReader(infile)
        # fieldnames = self.extend_fieldnames(r.fieldnames)
        fieldnames = r.fieldnames

        # Initialize the output for the results
        outfile = sys.stdout
        w = csv.DictWriter(outfile, fieldnames=fieldnames)
        w.writeheader()

        # Process each result
        for result in r:

            # Make up the arguments for the lookup call
            keyword_arguments = {}

            for parameter_name in args:
                keyword_arguments[parameter_name] = result.get(parameter_name, None)

            # Perform the lookup
            output = self.do_lookup(**keyword_arguments)

            # Put the output in the result
            if output:
                self.add_result(result, output, fieldnames, True)

            # Write out the result
            w.writerow(result)