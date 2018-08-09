import unittest

import responses

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

    def test_get_collection_exercises_for_survey_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_collection_exercises_by_survey, json=collection_exercise_by_survey, status=200)

            with app.app_context():
                collection_exercises = collection_exercise_controller.get_collection_exercises_for_survey(collection_exercise['surveyId'])

                self.assertTrue(collection_exercises is not None)

    def test_get_collection_exercises_for_survey_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_collection_exercises_by_survey, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    collection_exercise_controller.get_collection_exercises_for_survey(collection_exercise['surveyId'])
