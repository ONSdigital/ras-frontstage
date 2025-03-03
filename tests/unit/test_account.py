import unittest

from werkzeug.datastructures import ImmutableMultiDict

from frontstage.views.account.account import (
    check_attribute_change,
)


class TestAccount(unittest.TestCase):
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
