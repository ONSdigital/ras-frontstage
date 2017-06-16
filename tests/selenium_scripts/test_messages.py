import unittest
from selenium import webdriver
from test_send_message import SendMessage


class MessagesGet(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome(executable_path="/Users/irving/projects/webdriverio-test/chromedriver")
        self.driver.implicitly_wait(30)

    def test_no_messages(self):
        self.driver.get("http://localhost:5001/secure-message/messages")

        msg_list = self.driver.find_element_by_class_name("message-list")
        message = msg_list.find_element_by_tag_name("li")

        self.assertEqual(message.text, "You have no messages")

    def test_sent_messages(self):
        self.driver.get("http://0.0.0.0:5001/secure-message/create-message")
        SendMessage.send_message_test(self)
        self.driver.get("http://localhost:5001/secure-message/messages")
        self.driver.find_element_by_link_text("Sent").click()
        self.driver.find_element_by_link_text("Test Subject")

    def test_message_preview_given(self):
        self.driver.get("http://localhost:5001/secure-message/messages/SENT")
        body = self.driver.find_element_by_tag_name("p")
        self.assertEqual(body.text, "Test Body")

    def test_message_details(self):
        self.driver.get("http://localhost:5001/secure-message/messages/SENT")
        self.driver.find_element_by_link_text("Test Subject")
        self.driver.find_element_by_xpath("//*[contains(text(), 'respondent.000000000')]")
