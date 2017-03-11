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

class SplunkTestCase(object):

    username = 'admin'
    password = 'changeme'
    base_url = 'http://127.0.0.1:8000'
    browser_to_use = 'firefox'

    @staticmethod
    def remove_trailing_slash(url):
        """
        Remove the trailing slash from the URL if necessary.
        """

        if url[-1] == '/':
            return url[:-1]
        else:
            return url

    def do_login(self):
        """
        This function performs authentication with Splunk.
        """

        driver = self.driver
        driver.get(self.remove_trailing_slash(self.base_url) + "/en-US/account/login")
        driver.find_element_by_id("username").clear()
        driver.find_element_by_id("username").send_keys(self.username)
        driver.find_element_by_id("password").clear()
        driver.find_element_by_id("password").send_keys(self.password)
        driver.find_element_by_css_selector("input.splButton-primary.btn").click()
        self.assertTrue(self.is_element_present(By.CSS_SELECTOR, "a.manage-apps"))

    def get_browser_driver(self):
        """
        Makes an instance the browser driver that should be used.
        """

        # Make sure the browser is not None and is lowercase
        if self.browser_to_use is None:
            browser_to_use = 'firefox'
        else:
            browser_to_use = self.browser_to_use.lower()

        # Get the appropriate driver
        if browser_to_use == 'firefox':
            self.driver = webdriver.Firefox()
        elif browser_to_use == 'chrome':
            self.driver = webdriver.Chrome()
        else:
            raise Exception('Browser "%s" not recognized' % (browser_to_use))

        return self.driver

    # Create the updated setup function
    def setUp(self):
        """
        This is the updated setup function that is customized for Splunk tests.
        """

        self.get_browser_driver()

        # This is the content from the original setUp function made by SeleniumIDE
        self.driver.implicitly_wait(30)
        self.verificationErrors = []
        self.accept_next_alert = True

        # Now do the other things, like authenticating with Splunk
        self.do_login()

class UITestCaseLoader(object):
    """
    This class loads test cases and patches them so that the tests can run.
    """

    @staticmethod
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
            #print "Updating path to include selenium driver, path=%s, working_path=%s", full_driver_path, os.getcwd())

    @staticmethod
    def load_all_modules_from_dir(dirname, test_case=None):
        """
        This function loads test cases from the test-case directory.
        """

        cases_loaded = 0

        for (module_loader, name, ispkg) in pkgutil.iter_modules([dirname]):
            #importlib.import_module('ui_test_cases.' + name)

            #importlib.import_module('.' + name, __package__)
            if test_case is None or name == test_case:
                importlib.import_module('.' + name, 'ui_test_cases')
                cases_loaded += 1

        if cases_loaded == 0:
            raise Exception("No test cases were loaded")

    @classmethod
    def add_test_classes_to_suite(cls, suite, url, username, password, browser):
        """
        Create the classes with the necessary modification to perform the tests
        and add them to the given suite.
        """

        for test_case_class in unittest.TestCase.__subclasses__():

            if test_case_class.__name__ == "FunctionTestCase":
                continue

            # Make the new class for the test-case
            # This test case should include the name of the browser it will test and inherit from
            # the super-class that patches the underlying functions as needed.
            new_class = type(test_case_class.__name__ + browser.title(),
                             (SplunkTestCase, test_case_class), {})

            # Set up the defaults for when the test executes
            new_class.browser_to_use = browser.lower()
            new_class.base_url = url
            new_class.username = username
            new_class.password = password

            # Add the test class
            suite.addTest(unittest.makeSuite(new_class))


    @classmethod
    def load_test_suite(cls, url, username, password, test_case_dir='ui_test_cases',
                        browser='firefox', testcase=None):
        """
        Load the test cases from the test-case directory and create the classes
        with the necessary modification to perform the tests.
        """

        # Use a default browser
        if browser is None:
            browser = 'firefox'

        # Add the browser driver to the path
        cls.add_browser_driver_to_path()

        # Load the modules in the directory that appear to be test cases
        cls.load_all_modules_from_dir(test_case_dir, testcase)

        # Make a test suite
        suite = unittest.TestSuite()

        # Add the test classes
        for browser_to_test in browser.split(","):
            cls.add_test_classes_to_suite(suite, url, username, password, browser_to_test)

        return suite

    @classmethod
    def run_test_suite(cls, url='http://127.0.0.1:8000', username='admin', password='changeme',
                       test_case_dir='ui_test_cases', browser='firefox', testcase=None):
        """
        Load the tests that exist in the test-case directory and execute them.
        """

        suite = cls.load_test_suite(url, username, password, test_case_dir, browser, testcase)

        result = unittest.TextTestRunner(verbosity=2).run(suite)
        sys.exit(not result.wasSuccessful())


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


if __name__ == '__main__':

    # Parse the CLI arguments
    arguments = parse_args()

    UITestCaseLoader.run_test_suite(url=arguments.url, username=arguments.username, password=arguments.password, browser=arguments.browser, testcase=arguments.testcase)

