import unittest

from selenium import webdriver

from config import SecureMessaging


class TestDraft(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome(executable_path=SecureMessaging.chrome_driver)
        self.driver.implicitly_wait(30)

        # navigate to the create message page
        self.driver.get("http://0.0.0.0:5001/secure-message/create-message")

    def test_check_saved_draft(self):
        self.subject_field = self.driver.find_element_by_id("secure-message-subject").send_keys('Test Subject ')
        self.body_field = self.driver.find_element_by_id("secure-message-body").send_keys('Test Body ')
        self.driver.find_element_by_id("draft").click()
        self.assertTrue(self.driver.find_element_by_id('inbox-link'))

    def test_open_saved_draft(self):
        self.driver.get("http://0.0.0.0:5001/secure-message/messages/DRAFT")
        self.driver.find_element_by_link_text("Test Subject").click()
        self.assertTrue(self.driver.find_element_by_id('inbox-link'))

    def test_edit_saved_draft_then_save(self):
        self.driver.get("http://0.0.0.0:5001/secure-message/messages/DRAFT")
        self.driver.find_element_by_link_text("Test Subject").click()
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
