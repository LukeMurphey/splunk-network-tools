"""
This Python script loads test cases that were generated from the SeleniumIDE from a directory and
executes them.

The test cases need to be exported as Python 2 unittest WebDriver cases and placed in the
ui_test_cases directory.

This test runner is necessary in order to patch the test cases so that they work better with
Splunk. Specifically, this runner will update the tests such that they:

   1) Perform authentication  to Splunk before running the test cases
   2) Allow the use of browsers other than Firefox
"""

import os
import platform
import importlib
import sys
import unittest
import pkgutil
import argparse

from selenium import webdriver
from selenium.webdriver.common.by import By

def parse_args():
    """
    Create an argument parser for handling CLI parameters and return the parsed arguments.
    """

    parser = argparse.ArgumentParser(description='Run WebDriver UI tests exported by ' \
    + 'SeleniumIDE in a way that works with Splunk.')

    # Add the test case argument
    parser.add_argument('--testcase', help='the test case to run', default=None)

    # Add the Splunk Web URL argument
    parser.add_argument('--url', help='the URL of SplunkWeb', default='http://127.0.0.1:8000')

    # Add the Splunk username argument
    parser.add_argument('--username', help='the user account to use when authenticating to Splunk',
                        default='admin')

    # Add the Splunk password argument
    parser.add_argument('--password', help='the password to use when authenticating to Splunk',
                        default='changeme')

    # Add the browser argument
    parser.add_argument('--browser', help='the browser to use',
                        default=None)

    return parser.parse_args()

def remove_trailing_slash(url):
    """
    Remove the trailing slash from the URL if necessary.
    """

    if url[-1] == '/':
        return url[:-1]
    else:
        return url

# Parse the CLI arguments
ARGUMENTS = parse_args()

# Get the necessary parameters
SPLUNK_WEB_URL = remove_trailing_slash(ARGUMENTS.url)
SPLUNK_USERNAME = ARGUMENTS.username
SPLUNK_PASSWORD = ARGUMENTS.password
TEST_CASE_TO_RUN = ARGUMENTS.testcase
BROWSER_TO_USE = ARGUMENTS.browser

def add_browser_driver_to_path():
    """
    Add the browser driver to the path
    """

    driver_path = None

    if sys.platform == "linux2" and platform.architecture()[0] == '64bit':
        driver_path = "linux64"
    elif sys.platform == "linux2":
        driver_path = "linux32"
    else:
        driver_path = sys.platform

    full_driver_path = os.path.join(os.getcwd(), 'browser_drivers', driver_path)

    if not full_driver_path in os.environ["PATH"]:
        os.environ["PATH"] += ":" +full_driver_path
        #logger.debug("Updating path to include selenium driver, path=%s, working_path=%s", full_driver_path, os.getcwd())

def load_all_modules_from_dir(dirname):
    """
    This function loads test cases from the test-case directory.
    """
    cases_loaded = 0

    for (module_loader, name, ispkg) in pkgutil.iter_modules([dirname]):
        #importlib.import_module('ui_test_cases.' + name)

        #importlib.import_module('.' + name, __package__)
        if TEST_CASE_TO_RUN is None or name == TEST_CASE_TO_RUN:
            importlib.import_module('.' + name, 'ui_test_cases')
            cases_loaded += 1

    if cases_loaded == 0:
        raise Exception("No test cases were loaded")

def do_login(self):
    """
    This function performs authentication with Splunk.
    """

    driver = self.driver
    driver.get(SPLUNK_WEB_URL + "/en-US/account/login")
    driver.find_element_by_id("username").clear()
    driver.find_element_by_id("username").send_keys(SPLUNK_USERNAME)
    driver.find_element_by_id("password").clear()
    driver.find_element_by_id("password").send_keys(SPLUNK_PASSWORD)
    driver.find_element_by_css_selector("input.splButton-primary.btn").click()
    self.assertTrue(self.is_element_present(By.CSS_SELECTOR, "a.manage-apps"))

def get_browser_driver(self):
    """
    Makes an instance the browser driver that should be used.
    """

    if BROWSER_TO_USE is None:
        browser_to_use = 'firefox'

    self.browser_to_use = BROWSER_TO_USE.lower()

    if self.browser_to_use == 'firefox':
        self.driver = webdriver.Firefox()
    elif self.browser_to_use == 'chrome':
        self.driver = webdriver.Chrome()

    else:
        raise Exception('Browser "%s" not recognized' % (browser_to_use))

def patch_test_case(test_class):
    """
    Patch the test case so that local modifications can be used.
    """

    # Keep a copy of the original setup function since we will still want to call it in the patched
    # version.
    orig_setup = test_class.setUp

    # Create the updated setup function
    def new_setup(self):
        """
        This is the updated setup function that is customized for Splunk tests.
        """

        # Call the original
        #orig_setup(self)

        get_browser_driver(self)

        # This is the content from the original setUp function made by SeleniumIDE
        self.driver.implicitly_wait(30)
        self.base_url = SPLUNK_WEB_URL
        self.verificationErrors = []
        self.accept_next_alert = True

        # Now do the other things, like authenticating with Splunk
        do_login(self)

    # Patch the test case
    test_class.setUp = new_setup

    # Return the updated test case
    return test_class

# Add the browser driver to the path
add_browser_driver_to_path()

# Load the test cases
load_all_modules_from_dir('ui_test_cases')

# Make a test suite
suite = unittest.TestSuite()

for test_case_class in unittest.TestCase.__subclasses__()[1:]: # TODO: better handle this

    suite.addTest(unittest.makeSuite(patch_test_case(test_case_class)))

result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())

