import logging
import unittest
from requests.models import Response
from unittest.mock import patch

from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import ApiError
from tests.app.mocked_services import active_iac, case, collection_exercise, encoded_jwt_token, encrypted_enrolment_code,\
    enrolment_code, url_validate_enrolment

logger = wrap_logger(logging.getLogger(__name__))


class TestAddSurveySubmit(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie('localhost', 'authorization', 'session_key')
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
        }
        self.patcher = patch('redis.StrictRedis.get', return_value=encoded_jwt_token)

        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @patch('frontstage.controllers.party_controller.add_survey')
    @patch('frontstage.controllers.case_controller.post_case_event')
    @patch('frontstage.controllers.collection_exercise_controller.get_collection_exercise')
    @patch('frontstage.controllers.case_controller.get_case_by_enrolment_code')
    @patch('frontstage.controllers.iac_controller.get_iac_from_enrolment')
    @patch('frontstage.common.cryptographer.Cryptographer.decrypt')
    def test_add_survey_submit_success_redirect_to_survey_todo_list(self, decrypt_enrolment_code, get_iac_by_enrolment_code,
                                                                    get_case_by_enrolment, get_collection_exercise, *_):
        decrypt_enrolment_code.return_value = enrolment_code.encode()
        get_iac_by_enrolment_code.return_value = active_iac
        get_case_by_enrolment.return_value = case
        get_collection_exercise.return_value = collection_exercise

        response = self.app.get(f'/surveys/add-survey/add-survey-submit?encrypted_enrolment_code={encrypted_enrolment_code}')

        self.assertEqual(response.status_code, 302)
        self.assertTrue('/surveys/todo'.encode() in response.data)
        self.assertTrue(case['partyId'].encode() in response.data)
        self.assertTrue(collection_exercise['surveyId'].encode() in response.data)

    @patch('frontstage.controllers.iac_controller.get_iac_from_enrolment')
    @patch('frontstage.common.cryptographer.Cryptographer.decrypt')
    def test_add_survey_submit_fail(self, decrypt_enrolment_code, get_iac_from_enrolment):
        decrypt_enrolment_code.return_value = enrolment_code.encode()

        error_response = Response()
        error_response.status_code = 500
        error_response.url = url_validate_enrolment
        error = ApiError(logger, error_response)
        error.status_code = 500
        get_iac_from_enrolment.side_effect = error

        response = self.app.get(f'/surveys/add-survey/add-survey-submit?encrypted_enrolment_code={encrypted_enrolment_code}')

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Error 500 - Server error'.encode() in response.data)
