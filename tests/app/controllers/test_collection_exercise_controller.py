import unittest
from unittest.mock import patch

import responses

from config import TestingConfig
from frontstage import app
from frontstage.common.mappers import convert_events_to_new_format
from frontstage.controllers import collection_exercise_controller
from frontstage.exceptions.exceptions import ApiError
from tests.app.mocked_services import collection_exercise, collection_exercise_by_survey, survey, \
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

    @patch('frontstage.controllers.collection_exercise_controller.get_collection_exercises_for_survey')
    def test_get_live_collection_exercises_for_survey(self, get_collection_exercises_for_survey):
        for ce in collection_exercise_by_survey:
            if ce['events']:
                ce['events'] = convert_events_to_new_format(ce['events'])

        get_collection_exercises_for_survey.return_value = collection_exercise_by_survey

        live_collection_exercises = collection_exercise_controller.get_live_collection_exercises_for_survey(survey['id'])

        for live_collection_exercise in live_collection_exercises:
            self.assertEqual(live_collection_exercise['state'], 'LIVE')
            self.assertFalse(live_collection_exercise['events']['go_live']['is_in_future'])
