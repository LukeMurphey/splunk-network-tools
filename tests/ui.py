"""
This Python script loads test cases that were generated from the SeleniumIDE and executes them
against a running Splunk install. The purpose of this script is to make it possible to run tests
against Splunk without having to write code using WebDriver directly. Instead, the intent is that
testers write tests in the Selenium IDE GUI. This ought to make tests easier to write and maintain.

This is release under the Apache 2.0 Licence:

    https://www.apache.org/licenses/LICENSE-2.0

Why do I need this script?
----------------------------
There are several problems that tests exported from the Selenium IDE have when run against Splunk:

  1) The tests will not authenticate unless you manually add the authenticate steps (which means
     you would have to hard-code the credentials)
  2) The tests won't allow you to change which Splunk host to test against
  3) The tests work only for Firefox
  4) The tests have some default values that can make tests take too long (timeout is too high)

This test script solves all of these problems.


How do I use this script?
----------------------------
First, install Firefox install the following extensions:

  1) Selenium IDE (https://mzl.la/2qZ8Z7S)
  2) Test Suite Batch Converter (https://mzl.la/2rT7192)

You may want to install "Implicit Wait" (https://mzl.la/2qexEIj) too since some have reported that
it makes the tests in Firefox run smoother.

Second, download the Python Selenium bindings (https://pypi.python.org/pypi/selenium) and put them
in the same directory as this script. When done, you should have a directory named "selenium" in
the same directory as this script.

Third, put the necessary browser drivers in your path. Alternatively, you can place them in a
directory named "browser_drivers" next to this script since this script will try to find the
drivers in that directory too.

Once you do all of that setup, you are ready to make your tests.

Finally, setup your project with the tests:

  1) Make a directory named "ui_test_cases" within the same directory as this file
  2) Make sure the "ui_test_cases" directory has an __init__.py (i.e. make it a python module)
  3) Make your test cases in the Selenium IDE an save them
  4) Export your test cases or suite as "Python 2 Webdriver" tests; this should make python files
     within the "ui_test_cases" directory
  5) Run this script (see below for what arguments it takes)

When done, you should have a directory structure like this:

    splunkuitest.py
    selenium/          (the downloaded Python bindings)
    ui_test_cases/     (where you test case HTML files and Python test code goes)
    browser_drivers/   (if you want the test script to load your browser drivers too)

Once setup, you should be able to run tests like this:

    python splunkuitest.py

To see the options, run the command with the "--help" parameter:

    python splunkuitest.py --help


Tell me more about how this script works
----------------------------
This script includes a class named "SplunkTestCase" that includes some overrides to the default
test cases exported by Selenium IDE. This script will make new tests cases out of the exported
Selenium IDE tests that inherit from SplunkTestCase. Thus, the exported test cases are forced to
inherit from SplunkTestCase.

This script will also make copies of the test cases for each browser. Thus, if you have this test
against both Firefox and Chrome, you will get two tests for each original test (one for Firefox and
another for Chrome). The test case name will make it clear which browser it is testing so that you
can determine which test failed.
"""

import os
import platform
import importlib
import sys
import unittest
import pkgutil
import argparse

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
except ImportError:
    # Detect that the user didn't make Selenium available
    print 'Selenium could not be imported.\nMake sure to download the Python bindings' + \
    ' (https://pypi.python.org/pypi/selenium) and put it in "' + \
    os.path.dirname(os.path.realpath(__file__)) + \
    '".\nWhen done, you should have a directory named "selenium" (i.e. "' + \
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'selenium') + '"'
    sys.exit(1)

class SplunkTestCase(object):
    """
    This is a test that all exported WebDriver Selenium tests will be made to inherit from.
    Changes to this class will inherently affect all of the tests since the tests will inherit
    these functions.
    """

    username = 'admin'
    password = 'changeme'
    base_url = 'http://127.0.0.1:8000'
    browser_to_use = 'firefox'

    implicit_wait_time = 5

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
        # This was changed slightly to include a modifiable implicit wait time.
        # The original implicit wait time of 30 seconds could cause the loops for the "waitFor"
        # calls to take an extreme amount of time.
        self.driver.implicitly_wait(self.implicit_wait_time)
        self.verificationErrors = []
        self.accept_next_alert = True

        # Now do the other things, like authenticating with Splunk
        self.do_login()

class UITestCaseLoader(object):
    """
    This class loads test cases and patches them so that the tests can run.
    """

    @staticmethod
    def add_to_path(path_to_add):
        """
        Add the given path to the environment path unless it was already present. Return a boolean
        indicating if the path was updated.
        """

        if not path_to_add in os.environ["PATH"]:

            # Update the path according to the OS' expectations
            if sys.platform.startswith("win"):
                os.environ["PATH"] += ";" +path_to_add
            else:
                os.environ["PATH"] += ":" +path_to_add

            # Path was updated
            return True

        else:

            # Path was not updated
            return False

    @staticmethod
    def add_browser_driver_to_path():
        """
        Add the browser driver to the path
        """

        # First, add the base browser_drivers in case users didn't the drivers are not broken up
        # by architecture
        UITestCaseLoader.add_to_path(os.path.join(os.getcwd(), 'browser_drivers'))

        # Second, add the architecture specific path
        driver_path = None

        if sys.platform == "linux2" and platform.architecture()[0] == '64bit':
            driver_path = "linux64"
        elif sys.platform == "linux2":
            driver_path = "linux32"
        else:
            driver_path = sys.platform

        full_driver_path = os.path.join(os.getcwd(), 'browser_drivers', driver_path)

        UITestCaseLoader.add_to_path(full_driver_path)

    @staticmethod
    def load_all_modules_from_dir(dirname, test_case=None):
        """
        This function loads test cases from the test-case directory.
        """

        cases_loaded = 0

        for (_, name, _) in pkgutil.iter_modules([dirname]):

            if test_case is None or name.lower() == test_case.lower():

                try:
                    importlib.import_module('.' + name, 'ui_test_cases')
                except ImportError:
                    print 'Unable to import the test case in ui_test_cases.' + name + \
                    ', make sure that the ui_test_cases directory has an __init__.py file' + \
                    '(i.e. "' + os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ui_test_cases', '__init__.py') + ')"'

                    # Exit with a code that makes it clear we failed
                    sys.exit(1)

                cases_loaded += 1

        if cases_loaded == 0:

            if test_case is None:
                print 'No test cases were found. ' + \
                'Make sure that the tests are exported as Python 2 WebDriver tests to ' + \
                'the "ui_test_cases" directory (i.e. "' + \
                os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ui_test_cases') + ')"'
            else:
                print 'No test cases were found. ' + \
                'Your filter may just not match any of the tests.'

            # Exit with a code that makes it clear we failed
            sys.exit(1)

    @classmethod
    def add_test_classes_to_suite(cls, suite, url, username, password, browser, ignore_list=None):
        """
        Create the classes with the necessary modification to perform the tests
        and add them to the given suite.
        """

        for test_case_class in unittest.TestCase.__subclasses__():

            # Ignore any test in the ignore list
            if ignore_list is not None and test_case_class in ignore_list:
                print "ignoring", test_case_class
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

        # Keep a list of the existing cases so that we can know what is new
        # We are only going to run the next tests that were loaded from the test-case directory
        existing_tests = unittest.TestCase.__subclasses__()

        # Load the modules in the directory that appear to be test cases
        cls.load_all_modules_from_dir(test_case_dir, testcase)

        # Make a test suite
        suite = unittest.TestSuite()

        # Add the test classes
        for browser_to_test in browser.split(","):
            cls.add_test_classes_to_suite(suite, url, username, password, browser_to_test,
                                          existing_tests)

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
    parsed_arguments = parse_args()

    UITestCaseLoader.run_test_suite(url=parsed_arguments.url,
                                    username=parsed_arguments.username,
                                    password=parsed_arguments.password,
                                    browser=parsed_arguments.browser,
                                    testcase=parsed_arguments.testcase)
