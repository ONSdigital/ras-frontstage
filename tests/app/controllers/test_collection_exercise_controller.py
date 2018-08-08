import unittest
from unittest.mock import patch

import responses

from config import TestingConfig
from frontstage import app
from frontstage.common.mappers import convert_events_to_new_format
from frontstage.controllers import collection_exercise_controller
from frontstage.exceptions.exceptions import ApiError
from tests.app.mocked_services import business_party, collection_exercise, collection_exercise_by_survey, survey, \
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

    def test_get_enrolment_with_collection_exercise(self):
        enrolment = {
            "business_party": business_party,
            "enrolment_details": {
                "enrolmentStatus": "ENABLED",
                "name": survey['longName'],
                "surveyId": survey['id']
            },
            "survey": survey
        }

        enrolment_with_collection_exercises = collection_exercise_controller.link_enrolment_with_collection_exercise(enrolment, collection_exercise_by_survey)

        for enrolment_with_ce in enrolment_with_collection_exercises:
            self.assertTrue(enrolment_with_ce['collection_exercise'] is not None)

    @patch('frontstage.controllers.collection_exercise_controller.get_collection_exercises_for_survey')
    def test_get_enrolments_with_collection_exercises_returns_live_collection_exercises(self, get_ces_for_survey):
        for survey_collection_exercise in collection_exercise_by_survey:
            survey_collection_exercise['events'] = convert_events_to_new_format(survey_collection_exercise['events'])
        get_ces_for_survey.return_value = collection_exercise_by_survey
        enrolments = [{
            "business_party": business_party,
            "enrolment_details": {
                "enrolmentStatus": "ENABLED",
                "name": survey['longName'],
                "surveyId": survey['id']
            },
            "survey": survey
        }]

        enrolments_with_collection_exercises = collection_exercise_controller.get_enrolments_with_collection_exercises(enrolments)

        for enrolment in enrolments_with_collection_exercises:
            self.assertTrue(enrolment['collection_exercise'] is not None, "Enrolment is missing expected collection exercise")
            self.assertEqual(enrolment['collection_exercise']['state'], 'LIVE', "Collection exercise returned that is not in live state")
