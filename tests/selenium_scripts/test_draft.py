import unittest
from selenium import webdriver

from app.config import SecureMessaging


class TestDraft(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome(executable_path=SecureMessaging.chrome_driver)
        self.driver.implicitly_wait(30)

        # navigate to the create message page
        self.driver.get("http://0.0.0.0:5001/secure-message/create-message")

    def save_message_test(self):
        # Save a draft
        self.subject_field = self.driver.find_element_by_id("secure-message-subject").send_keys('Test Subject ')
        self.body_field = self.driver.find_element_by_id("secure-message-body").send_keys('Test Body ')
        self.driver.find_element_by_id("draft").click()
        self.assertTrue(self.driver.find_element_by_id('inbox-link'))

        # Open a saved draft
        self.driver.get("http://0.0.0.0:5001/secure-message/messages/DRAFT")
        self.driver.find_element_by_link_text("Test Subject").click()
        self.assertTrue(self.driver.find_element_by_id('inbox-link'))

        # Change text in draft and save
        self.subject_field = self.driver.find_element_by_id("secure-message-subject").send_keys('Edited')
        self.body_field = self.driver.find_element_by_id("secure-message-body").send_keys('Edited')
        self.driver.find_element_by_id("draft").click()
        self.assertTrue(self.driver.find_element_by_id('inbox-link'))

    def tearDown(self):
        # close the browser window
        print("Closing browser")
        self.driver.quit()

if __name__ == '__main__':
    unittest.main()
