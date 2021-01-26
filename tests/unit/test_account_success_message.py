import unittest

from frontstage.views.account.account import create_success_message


class TestAccountSuccessMessage(unittest.TestCase):

    def test_message_success_with_three_attributes(self):
        attr = ['first_name', 'second_name', 'third_name']
        message = 'We have updated '
        actual_message = create_success_message(attr, message)
        expected_message = 'We have updated first_name, second_name and third_name'
        self.assertTrue(actual_message == expected_message)

    def test_message_success_with_two_attributes(self):
        attr = ['first_name', 'second_name']
        message = 'We have updated '
        actual_message = create_success_message(attr, message)
        expected_message = 'We have updated first_name and second_name'
        self.assertTrue(actual_message == expected_message)

    def test_message_success_with_single_attribute(self):
        attr = ['first_name']
        message = 'We have updated '
        actual_message = create_success_message(attr, message)
        expected_message = 'We have updated first_name'
        self.assertTrue(actual_message == expected_message)

    def test_message_success_with_four_attributes(self):
        attr = ['first_name', 'second_name', 'third_name', 'email']
        message = 'We have updated '
        actual_message = create_success_message(attr, message)
        expected_message = 'We have updated first_name, second_name, third_name and email'
        self.assertTrue(actual_message == expected_message)

    def test_message_success_with_no_attributes(self):
        attr = []
        message = 'We have updated '
        actual_message = create_success_message(attr, message)
        expected_message = 'We have updated '
        self.assertTrue(actual_message == expected_message)