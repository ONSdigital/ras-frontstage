import unittest
from datetime import datetime, timedelta

from frontstage.controllers.collection_exercise_controller import ordinal_date_formatter, due_date_convertor


class TestCollectionExerciseStaticFunctions(unittest.TestCase):

    def test_ordinal_date_formatter_for_st(self):
        fist_jan = datetime(2009, 1, 1, 0, 0)
        response = ordinal_date_formatter('{S} %B %Y, %H:%M', fist_jan)
        self.assertEqual('1st January 2009, 00:00', response)

    def test_ordinal_date_formatter_for_nd(self):
        fist_jan = datetime(2009, 1, 2, 0, 0)
        response = ordinal_date_formatter('{S} %B %Y, %H:%M', fist_jan)
        self.assertEqual('2nd January 2009, 00:00', response)

    def test_ordinal_date_formatter_for_th(self):
        fist_jan = datetime(2009, 1, 20, 0, 0)
        response = ordinal_date_formatter('{S} %B %Y, %H:%M', fist_jan)
        self.assertEqual('20th January 2009, 00:00', response)

    def test_due_date_convertor_for_today(self):
        today = datetime.now() + timedelta(seconds=60)
        response = due_date_convertor(today)
        self.assertEqual('Due today', response)

    def test_due_date_convertor_for_tomorrow(self):
        today = datetime.now() + timedelta(days=1)
        response = due_date_convertor(today)
        self.assertEqual('Due tomorrow', response)

    def test_due_date_convertor_for_days(self):
        today = datetime.now() + timedelta(days=3)
        response = due_date_convertor(today)
        self.assertEqual('Due in 2 days', response)

    def test_due_date_convertor_for_a_month(self):
        today = datetime.now() + timedelta(days=30)
        response = due_date_convertor(today)
        self.assertEqual('Due in a month', response)

    def test_due_date_convertor_for_two_month(self):
        today = datetime.now() + timedelta(days=60)
        response = due_date_convertor(today)
        self.assertEqual('Due in 2 months', response)

    def test_due_date_convertor_for_three_month(self):
        today = datetime.now() + timedelta(days=90)
        response = due_date_convertor(today)
        self.assertEqual('Due in 3 months', response)

    def test_due_date_convertor_for_over_three_month(self):
        today = datetime.now() + timedelta(days=120)
        response = due_date_convertor(today)
        self.assertEqual('Due in over 3 months', response)

    def test_due_date_convertor_date_in_past(self):
        today = datetime.now() - timedelta(days=120)
        response = due_date_convertor(today)
        self.assertEqual(None, response)
