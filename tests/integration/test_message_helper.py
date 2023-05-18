import json
import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

from frontstage.common.message_helper import (
    convert_to_bst,
    from_internal,
    get_formatted_date,
    refine,
)

with open("tests/test_data/message.json") as json_data:
    test_conversation_data = json.load(json_data)


class TestMessageHelper(unittest.TestCase):
    def test_from_internal(self):
        expected_data = {
            "subject": "testy2",
            "survey_id": "02b9c366-7397-42f7-942a-76dc5876d86d",
            "thread_id": "9e3465c0-9172-4974-a7d1-3a01592d1594",
            "from": "ONS Business Surveys Team",
            "from_internal": True,
            "internal_user": "0282d2f8-d96d-4fd9-bb7a-c1d781c0978f",
            "ru_ref": "e359b838-0d89-43e8-b5d0-68079916de80",
            "sent_date": "02 Apr 2018 10:27",
            "body": "something else",
            "message_id": "2ac51b39-a0d7-465d-92a4-263dfe3eb475",
            "unread": False,
        }
        test_copy = test_conversation_data.copy()
        test_copy["from_internal"] = True
        test_copy["internal_user"] = "0282d2f8-d96d-4fd9-bb7a-c1d781c0978f"
        refined_message = refine(test_copy)
        self.assertEqual(refined_message, expected_data)

    def test_get_formatted_date_incorrect_date(self):
        date_str = "018-04-04 09:27:11.354399"
        refined_date = get_formatted_date(date_str)
        self.assertEqual(refined_date, "018-04-04 09:27:11.354399")

    def test_get_formatted_date_today_date(self):
        with patch("frontstage.common.message_helper.date") as mock_date:
            mock_date.today.return_value = date(2018, 6, 12)
            today_example_date = get_formatted_date("2018-06-12 14:15:12")
            self.assertEqual(today_example_date, "Today at 15:15")

    def test_get_formatted_date_yesterday_date(self):
        with patch("frontstage.common.message_helper.date") as mock_date:
            mock_date.today.return_value = date(2018, 2, 12)
            yesterday_example_date = get_formatted_date("2018-02-11 14:15:12")
            self.assertEqual(yesterday_example_date, "Yesterday at 14:15")

    def test_get_formatted_date_multiple_days_ago(self):
        # 2 days ago
        past_date = datetime(2018, 2, 13, 10, 15, 15) - timedelta(2)
        formatted_date = get_formatted_date(past_date.strftime("%Y-%m-%d %H:%M:%S"))
        self.assertEqual(formatted_date, "11 Feb 2018 10:15")

    def test_missing_date(self):
        test_copy = test_conversation_data.copy()
        del test_copy["sent_date"]

        expected_data = {
            "subject": "testy2",
            "survey_id": "02b9c366-7397-42f7-942a-76dc5876d86d",
            "thread_id": "9e3465c0-9172-4974-a7d1-3a01592d1594",
            "from": "Peter Griffin",
            "from_internal": False,
            "internal_user": "GROUP",
            "ru_ref": "e359b838-0d89-43e8-b5d0-68079916de80",
            "sent_date": None,
            "body": "something else",
            "message_id": "2ac51b39-a0d7-465d-92a4-263dfe3eb475",
            "unread": False,
        }

        refined_message = refine(test_copy)
        self.assertEqual(refined_message, expected_data)

    def test_missing_subject(self):
        test_copy = test_conversation_data.copy()
        del test_copy["subject"]
        with self.assertRaises(KeyError):
            refine(test_copy)

    def test_missing_name(self):
        test_copy = test_conversation_data.copy()
        del test_copy["@msg_from"]
        with self.assertRaises(KeyError):
            refine(test_copy)

    def test_missing_business_id(self):
        test_copy = test_conversation_data.copy()
        del test_copy["@business_details"]
        with self.assertRaises(KeyError):
            refine(test_copy)

    def test_refine(self):
        expected_data = {
            "subject": "testy2",
            "survey_id": "02b9c366-7397-42f7-942a-76dc5876d86d",
            "thread_id": "9e3465c0-9172-4974-a7d1-3a01592d1594",
            "from": "Peter Griffin",
            "from_internal": False,
            "internal_user": "GROUP",
            "ru_ref": "e359b838-0d89-43e8-b5d0-68079916de80",
            "sent_date": "02 Apr 2018 10:27",
            "body": "something else",
            "message_id": "2ac51b39-a0d7-465d-92a4-263dfe3eb475",
            "unread": False,
        }

        refined_message = refine(test_conversation_data)
        self.assertEqual(refined_message, expected_data)

    def test_convert_to_bst_from_utc_during_bst(self):
        # 13th Jun 2018 at 14.12 should return 13th Jun 2018 at 15.12
        datetime_parsed = datetime(2018, 6, 13, 14, 12, 0, tzinfo=timezone.utc)
        returned_datetime = convert_to_bst(datetime_parsed)
        # Check date returned is in BST format
        self.assertEqual(datetime.strftime(returned_datetime, "%Y-%m-%d %H:%M:%S"), "2018-06-13 15:12:00")

    def test_convert_to_bst_from_utc_during_gmt(self):
        # 13th Feb 2018 at 14.12 should return 13th Feb 2018 at 14.12
        datetime_parsed = datetime(2018, 2, 13, 14, 12, 0, tzinfo=timezone.utc)
        returned_datetime = convert_to_bst(datetime_parsed)
        # Check date returned is in BST format
        self.assertEqual(datetime.strftime(returned_datetime, "%Y-%m-%d %H:%M:%S"), "2018-02-13 14:12:00")

    def test_from_internal_returns_false_if_not_specified(self):
        test_dict = {}

        is_from_internal = from_internal(test_dict)
        self.assertFalse(is_from_internal)

    def test_from_internal_returns_value_of_from_internal(self):
        test_dict = {"from_internal": True}

        is_from_internal = from_internal(test_dict)
        self.assertTrue(is_from_internal)
