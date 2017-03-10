# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
import unittest, time, re

class WakeOnLan(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(30)
        self.base_url = "http://127.0.0.1:8000/"
        self.verificationErrors = []
        self.accept_next_alert = True
    
    def test_wake_on_lan(self):
        driver = self.driver
        driver.get(self.base_url + "/en-US/app/network_tools/wakeonlan")
        for i in range(60):
            try:
                if 1 == len(driver.find_elements_by_css_selector("#table")): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        driver.find_element_by_link_text("Create a New Host").click()
        for i in range(60):
            try:
                if driver.find_element_by_id("inputName").is_displayed(): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        driver.find_element_by_id("inputName").clear()
        driver.find_element_by_id("inputName").send_keys("test")
        driver.find_element_by_id("inputMAC").clear()
        driver.find_element_by_id("inputMAC").send_keys("00:11:22:33:44:")
        driver.find_element_by_id("save-host").click()
        self.assertEqual("A valid MAC address must be provided (like 00:11:22:33:44:55)", driver.find_element_by_css_selector("#inputMAC + .help-inline").text)
    
    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException as e: return False
        return True
    
    def is_alert_present(self):
        try: self.driver.switch_to_alert()
        except NoAlertPresentException as e: return False
        return True
    
    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally: self.accept_next_alert = True
    
    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
