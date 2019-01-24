import unittest

import responses
from iso8601 import ParseError

from config import TestingConfig
from frontstage import app
from frontstage.controllers import collection_exercise_controller
from frontstage.exceptions.exceptions import ApiError
from tests.app.mocked_services import collection_exercise, collection_exercise_by_survey, \
    url_get_collection_exercises_by_survey


class TestCollectionExerciseController(unittest.TestCase):

    def setUp(self):
        app_config = TestingConfig()
        app.config.from_object(app_config)
        self.app = app.test_client()
        self.app_config = self.app.application.config

    def test_get_collection_exercises_for_survey_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_collection_exercises_by_survey, json=collection_exercise_by_survey, status=200)

            with app.app_context():
                collection_exercises = collection_exercise_controller.\
                    get_collection_exercises_for_survey(self.app_config, collection_exercise['surveyId'])

                self.assertTrue(collection_exercises is not None)

    def test_get_collection_exercises_for_survey_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_collection_exercises_by_survey, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    collection_exercise_controller.\
                        get_collection_exercises_for_survey(self.app_config, collection_exercise['surveyId'])

    def test_convert_events_to_new_format_successful(self):
        formatted_events = collection_exercise_controller.convert_events_to_new_format(collection_exercise['events'])

        self.assertTrue(formatted_events['go_live'] is not None)
        self.assertTrue(formatted_events['go_live']['date'] is not None)
        self.assertTrue(formatted_events['go_live']['is_in_future'] is not None)

    def test_convert_events_to_new_format_fail(self):
        events = [{
            "timestamp": "abc"
        }]

        with self.assertRaises(ParseError):
            collection_exercise_controller.convert_events_to_new_format(events)
