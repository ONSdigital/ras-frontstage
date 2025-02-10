import unittest
from datetime import datetime, timedelta

import responses
from iso8601 import ParseError

from config import TestingConfig
from frontstage import app
from frontstage.controllers import collection_exercise_controller
from frontstage.controllers.collection_exercise_controller import (
    due_date_converter,
    ordinal_date_formatter,
)
from frontstage.exceptions.exceptions import ApiError
from tests.integration.mocked_services import (
    collection_exercise,
    collection_exercise_by_survey,
    url_get_collection_exercises_by_surveys,
)


class TestCollectionExerciseController(unittest.TestCase):
    def setUp(self):
        app_config = TestingConfig()
        app.config.from_object(app_config)
        self.app = app.test_client()
        self.app_config = self.app.application.config

    def test_get_collection_exercises_for_survey_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_collection_exercises_by_surveys, json=collection_exercise_by_survey, status=200)

            with app.app_context():
                collection_exercises = collection_exercise_controller.get_collection_exercises_for_surveys(
                    [collection_exercise["surveyId"]],
                )

                self.assertTrue(collection_exercises is not None)

    def test_get_collection_exercises_for_survey_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_collection_exercises_by_surveys, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    collection_exercise_controller.get_collection_exercises_for_surveys(
                        [collection_exercise["surveyId"]],
                    )

    def test_get_collection_exercises_for_survey_no_exercises(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_collection_exercises_by_surveys, status=204)

            with app.app_context():
                collection_exercises = collection_exercise_controller.get_collection_exercises_for_surveys(
                    [collection_exercise["surveyId"]],
                )

                self.assertListEqual(collection_exercises, [])

    def test_convert_events_to_new_format_successful(self):
        formatted_events = collection_exercise_controller.convert_events_to_new_format(collection_exercise["events"])

        self.assertTrue(formatted_events["go_live"] is not None)
        self.assertTrue(formatted_events["go_live"]["date"] is not None)
        self.assertTrue(formatted_events["go_live"]["is_in_future"] is not None)

    def test_convert_events_to_new_format_fail(self):
        events = [{"timestamp": "abc"}]

        with self.assertRaises(ParseError):
            collection_exercise_controller.convert_events_to_new_format(events)

    def test_ordinal_date_formatter_for_st(self):
        fist_jan = datetime(2009, 1, 1, 0, 0)
        response = ordinal_date_formatter("{S} %B %Y, %H:%M", fist_jan)
        self.assertEqual("1st January 2009, 00:00", response)

    def test_ordinal_date_formatter_for_nd(self):
        fist_jan = datetime(2009, 1, 2, 0, 0)
        response = ordinal_date_formatter("{S} %B %Y, %H:%M", fist_jan)
        self.assertEqual("2nd January 2009, 00:00", response)

    def test_ordinal_date_formatter_for_th(self):
        fist_jan = datetime(2009, 1, 20, 0, 0)
        response = ordinal_date_formatter("{S} %B %Y, %H:%M", fist_jan)
        self.assertEqual("20th January 2009, 00:00", response)

    def test_due_date_convertor_for_today(self):
        today = datetime.now() + timedelta(seconds=60)
        response = due_date_converter(today)
        self.assertEqual("Due today", response)

    def test_due_date_convertor_for_tomorrow(self):
        today = datetime.now() + timedelta(days=1)
        response = due_date_converter(today)
        self.assertEqual("Due tomorrow", response)

    def test_due_date_convertor_for_days(self):
        today = datetime.now() + timedelta(days=3)
        response = due_date_converter(today)
        self.assertEqual("Due in 2 days", response)

    def test_due_date_convertor_for_a_month(self):
        today = datetime.now() + timedelta(days=30)
        response = due_date_converter(today)
        self.assertEqual("Due in a month", response)

    def test_due_date_convertor_for_two_month(self):
        today = datetime.now() + timedelta(days=60)
        response = due_date_converter(today)
        self.assertEqual("Due in 2 months", response)

    def test_due_date_convertor_for_three_month(self):
        today = datetime.now() + timedelta(days=90)
        response = due_date_converter(today)
        self.assertEqual("Due in 3 months", response)

    def test_due_date_convertor_for_over_three_month(self):
        today = datetime.now() + timedelta(days=120)
        response = due_date_converter(today)
        self.assertEqual("Due in over 3 months", response)

    def test_due_date_convertor_date_in_past(self):
        today = datetime.now() - timedelta(days=120)
        response = due_date_converter(today)
        self.assertEqual(None, response)
