"""
This Python script loads test cases from a directory

Define some resources that we will use for patching the test cases so that they run in Splunk
The updates will:
   1) Perform authentication before running the test cases
   2) Allow the use of browsers other than Firefox
"""

import os
import platform
import importlib
import sys
import unittest
import pkgutil

from selenium.webdriver.common.by import By

# Put the browser drivers on the path
#full_driver_path = os.path.join(os.getcwd(), 'browser_drivers', 'darwin')

#if not full_driver_path in os.environ["PATH"]:
#    os.environ["PATH"] += ":" +full_driver_path

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

add_browser_driver_to_path()

# This function will load the test cases
def load_all_modules_from_dir(dirname):
    """
    This function loads all modules in a given directory.
    """

    """
    for importer, package_name, _ in pkgutil.iter_modules([dirname]):
        full_package_name = '%s.%s' % (dirname, package_name)
        if full_package_name not in sys.modules:
            module = importer.find_module(package_name).load_module(full_package_name)
            print "Loading module: ", module
    """

    for (module_loader, name, ispkg) in pkgutil.iter_modules([dirname]):
        #print __package__ + '.' + name
        #importlib.import_module('ui_test_cases.' + name)

        #importlib.import_module('.' + name, __package__)
        importlib.import_module('.' + name, 'ui_test_cases')

# This function will perform authentication with Splunk
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

# This function will patch a test class 
def patch_test_case(test_class):
    """
    Update the test accordingly.
    """

    orig_setUp = test_class.setUp

    def newSetUp(self):
        orig_setUp(self)
        do_login(self)

    test_class.setUp = newSetUp

    return test_class

# Load the test cases
load_all_modules_from_dir('ui_test_cases')

# Make a test suite
suite = unittest.TestSuite()

for test_case_class in unittest.TestCase.__subclasses__()[1:]:
    #print test_case_class
    suite.addTest(unittest.makeSuite(patch_test_case(test_case_class)))
    #suite.addTest (test_case_class())
    #suite.addTest(test_case_class())
    #test_cases.append(patch_test_case(test_case_class))


#from ui_test_cases.Ping import Ping

#suite = unittest.TestSuite()
#suite.addTest(unittest.makeSuite(Ping))

result = unittest.TextTestRunner(verbosity=2).run(suite)

#if __name__ == "__main__":
#    unittest.main()