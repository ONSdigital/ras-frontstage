# -*- coding: utf-8 -*-
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time

success = True
wd = WebDriver()
wd.implicitly_wait(60)

def is_alert_present(wd):
    try:
        wd.switch_to_alert().text
        return True
    except:
        return False

try:
    wd.get("http://0.0.0.0:5001/secure-message/create-message")
    wd.find_element_by_id("secure-message-subject").click()
    wd.find_element_by_id("secure-message-subject").clear()
    wd.find_element_by_id("secure-message-subject").send_keys("tEST SUBJECT")
    wd.find_element_by_id("secure-message-body").click()
    wd.find_element_by_id("secure-message-body").clear()
    wd.find_element_by_id("secure-message-body").send_keys("TEST BODY")
    wd.find_element_by_css_selector("input.btn").click()
finally:
    wd.quit()
    if not success:
        raise Exception("Test failed.")
