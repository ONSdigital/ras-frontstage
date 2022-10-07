import unittest

from werkzeug.datastructures import ImmutableMultiDict

from frontstage.views.account.account import (
    check_attribute_change,
    create_success_message,
)


class TestAccount(unittest.TestCase):
    def test_message_success_with_three_attributes(self):
        attr = ["first_name", "second_name", "third_name"]
        message = "We have updated "
        actual_message = create_success_message(attr, message)
        expected_message = "We have updated first_name, second_name and third_name"
        self.assertTrue(actual_message == expected_message)

    def test_message_success_with_two_attributes(self):
        attr = ["first_name", "second_name"]
        message = "We have updated "
        actual_message = create_success_message(attr, message)
        expected_message = "We have updated first_name and second_name"
        self.assertTrue(actual_message == expected_message)

    def test_message_success_with_single_attribute(self):
        attr = ["first_name"]
        message = "We have updated "
        actual_message = create_success_message(attr, message)
        expected_message = "We have updated first_name"
        self.assertTrue(actual_message == expected_message)

    def test_message_success_with_four_attributes(self):
        attr = ["first_name", "second_name", "third_name", "email"]
        message = "We have updated "
        actual_message = create_success_message(attr, message)
        expected_message = "We have updated first_name, second_name, third_name and email"
        self.assertTrue(actual_message == expected_message)

    def test_message_success_with_no_attributes(self):
        attr = []
        message = "We have updated "
        actual_message = create_success_message(attr, message)
        expected_message = "We have updated "
        self.assertTrue(actual_message == expected_message)

    def test_check_attribute_change_returns_true(self):
        first_name = FormData("something")
        last_name = FormData("test")
        telephone = FormData("07234765346")
        form = ImmutableMultiDict([("first_name", first_name), ("last_name", last_name), ("phone_number", telephone)])
        attributes_changed = []
        respondent_details = {"firstName": "test", "lastName": "test", "telephone": "07234765346"}
        update_required_flag = False
        update_required_flag = check_attribute_change(
            form, attributes_changed, respondent_details, update_required_flag
        )
        self.assertTrue(update_required_flag)
        self.assertEqual(["first name"], attributes_changed)

    def test_check_attribute_change_return_false(self):
        first_name = FormData("test")
        last_name = FormData("test")
        telephone = FormData("07234765346")
        form = ImmutableMultiDict([("first_name", first_name), ("last_name", last_name), ("phone_number", telephone)])
        attributes_changed = []
        respondent_details = {"firstName": "test", "lastName": "test", "telephone": "07234765346"}
        update_required_flag = False
        update_required_flag = check_attribute_change(
            form, attributes_changed, respondent_details, update_required_flag
        )
        self.assertFalse(update_required_flag)
        self.assertEqual([], attributes_changed)


class FormData:
    def __init__(self, data):
        self.data = data
