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

from selenium.webdriver.common.by import By

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

    for (module_loader, name, ispkg) in pkgutil.iter_modules([dirname]):
        #importlib.import_module('ui_test_cases.' + name)

        #importlib.import_module('.' + name, __package__)
        importlib.import_module('.' + name, 'ui_test_cases')

def do_login(self):
    """
    This function performs authentication with Splunk.
    """

    driver = self.driver
    driver.get("http://127.0.0.1:8000/en-US/account/login")
    driver.find_element_by_id("username").clear()
    driver.find_element_by_id("username").send_keys("admin")
    driver.find_element_by_id("password").clear()
    driver.find_element_by_id("password").send_keys("changeme")
    driver.find_element_by_css_selector("input.splButton-primary.btn").click()
    self.assertTrue(self.is_element_present(By.CSS_SELECTOR, "a.manage-apps"))

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
        orig_setup(self)

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

for test_case_class in unittest.TestCase.__subclasses__()[1:]:
    suite.addTest(unittest.makeSuite(patch_test_case(test_case_class)))

result = unittest.TextTestRunner(verbosity=2).run(suite)
