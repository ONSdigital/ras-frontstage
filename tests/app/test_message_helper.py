import unittest
import json

from datetime import datetime, timedelta
from frontstage.common.message_helper import refine, get_formatted_date

with open('tests/test_data/conversation.json') as json_data:
    test_data = json.load(json_data)

refined_data = {"subject": "testy2", "survey_id": "02b9c366-7397-42f7-942a-76dc5876d86d", "thread_id": "9e3465c0-9172-4974-a7d1-3a01592d1594",
                "from": "Peter Griffin", "ru_ref": "e359b838-0d89-43e8-b5d0-68079916de80", "sent_date": "02 Apr 2018 09:27",
                "body": "something else", "message_id": "2ac51b39-a0d7-465d-92a4-263dfe3eb475", "unread": False}


class TestMessageHelper(unittest.TestCase):

    def test_from_internal(self):
        test_copy = test_data.copy()
        test_copy['from_internal'] = True
        refined_data_copy = refined_data.copy()
        refined_data_copy['from'] = "ONS Business Surveys Team"
        refined_message = refine(test_copy)
        self.assertEqual(refined_message, refined_data_copy)

    def test_get_formatted_date_incorrect_date(self):
        date_str = "018-04-04 09:27:11.354399"
        refined_date = get_formatted_date(date_str)
        self.assertEqual(refined_date, "018-04-04 09:27:11.354399")

    def test_get_formatted_date_today_date(self):
        today_date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        today_time_str = datetime.now().strftime('%H:%M')
        refined_date = get_formatted_date(today_date_str)
        self.assertEqual(refined_date, "Today at " + today_time_str)

    def test_get_formatted_date_yesterday_date(self):
        yesterday_date = datetime.now() - timedelta(1)
        yesterday_date_str = yesterday_date.strftime('%Y-%m-%d %H:%M:%S')
        yesterday_time_str = datetime.now().strftime('%H:%M')
        refined_date = get_formatted_date(yesterday_date_str)
        self.assertEqual(refined_date, "Yesterday at " + yesterday_time_str)

    def test_get_formatted_date_multiple_days_ago(self):
        # 2 days ago
        past_date = datetime.now() - timedelta(2)
        past_date_str = past_date.strftime('%Y-%m-%d %H:%M:%S')
        refined_past_date = past_date.strftime('%d %b %Y %H:%M')
        refined_date = get_formatted_date(past_date_str)
        self.assertEqual(refined_date, refined_past_date)

    def test_missing_date(self):
        test_copy = test_data.copy()
        del test_copy['sent_date']
        refined_data_copy = refined_data.copy()
        refined_data_copy['sent_date'] = None
        refined_message = refine(test_copy)
        self.assertEqual(refined_message, refined_data_copy)

    def test_missing_subject(self):
        test_copy = test_data.copy()
        del test_copy['subject']
        with self.assertRaises(KeyError):
            refine(test_copy)

    def test_missing_name(self):
        test_copy = test_data.copy()
        del test_copy['@msg_from']
        with self.assertRaises(KeyError):
            refine(test_copy)

    def test_missing_ru_id(self):
        test_copy = test_data.copy()
        del test_copy['@ru_id']
        with self.assertRaises(KeyError):
            refine(test_copy)

    def test_refine(self):
        refined_message = refine(test_data)
        self.assertEqual(refined_message, refined_data)
