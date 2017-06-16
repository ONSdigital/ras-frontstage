import unittest
from selenium import webdriver
from test_send_message import SendMessage
from app.config import SecureMessaging


class MessagesGet(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Chrome(executable_path=SecureMessaging.chrome_driver)
        self.driver.implicitly_wait(30)

    def test_no_messages(self):
        self.driver.get(SecureMessaging.MESSAGES_UI_URL)

        msg_list = self.driver.find_element_by_class_name("message-list")
        message = msg_list.find_element_by_tag_name("li")

        self.assertEqual(message.text, "You have no messages")

    def test_sent_messages(self):
        self.driver.get(SecureMessaging.CREATE_MESSAGE_UI_URL)
        SendMessage.send_message_test(self)
        self.driver.get(SecureMessaging.MESSAGES_UI_URL)
        self.driver.find_element_by_link_text("Sent").click()
        self.driver.find_element_by_link_text("Test Subject")

    def test_message_preview_given(self):
        self.driver.get(SecureMessaging.MESSAGES_UI_URL + '/SENT')
        body = self.driver.find_element_by_tag_name("p")
        self.assertEqual(body.text, "Test Body")

    def test_message_details(self):
        self.driver.get(SecureMessaging.MESSAGES_UI_URL + '/SENT')
        self.driver.find_element_by_link_text("Test Subject")
        self.driver.find_element_by_xpath("//*[contains(text(), 'respondent.000000000')]")
