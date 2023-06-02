import json
import logging
import unittest
from unittest.mock import patch

import requests_mock
from requests.models import Response
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import ApiError
from frontstage.views.surveys.add_survey_submit import (
    is_respondent_and_business_enrolled,
)
from tests.integration.mocked_services import (
    active_iac,
    business_party,
    case,
    case_diff_surveyId,
    collection_exercise,
    encoded_jwt_token,
    encrypted_enrolment_code,
    enrolment_code,
    url_banner_api,
    url_validate_enrolment,
)

logger = wrap_logger(logging.getLogger(__name__))


class TestAddSurveySubmit(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie("localhost", "authorization", "session_key")
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
        }
        self.patcher = patch("redis.StrictRedis.get", return_value=encoded_jwt_token)

        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.add_survey")
    @patch("frontstage.controllers.case_controller.post_case_event")
    @patch("frontstage.controllers.party_controller.get_party_by_business_id")
    @patch("frontstage.controllers.collection_exercise_controller.get_collection_exercise")
    @patch("frontstage.controllers.case_controller.get_case_by_enrolment_code")
    @patch("frontstage.controllers.iac_controller.get_iac_from_enrolment")
    @patch("frontstage.common.cryptographer.Cryptographer.decrypt")
    def test_add_survey_submit_success_redirect_to_survey_todo_list(
        self,
        mock_request,
        decrypt_enrolment_code,
        get_iac_from_enrolment_code,
        get_case_by_enrolment,
        get_collection_exercise,
        get_party_by_business_id,
        *_,
    ):
        mock_request.get(url_banner_api, status_code=404)
        decrypt_enrolment_code.return_value = enrolment_code.encode()
        get_iac_from_enrolment_code.return_value = active_iac
        get_case_by_enrolment.return_value = case
        get_collection_exercise.return_value = collection_exercise
        get_party_by_business_id.return_value = business_party

        response = self.app.get(
            f"/surveys/add-survey/add-survey-submit?encrypted_enrolment_code={encrypted_enrolment_code}"
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue("/surveys/todo".encode() in response.data)
        self.assertTrue(case["partyId"].encode() in response.data)
        self.assertTrue(collection_exercise["surveyId"].encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.add_survey")
    @patch("frontstage.controllers.case_controller.post_case_event")
    @patch("frontstage.controllers.party_controller.get_party_by_business_id")
    @patch("frontstage.controllers.collection_exercise_controller.get_collection_exercise")
    @patch("frontstage.controllers.case_controller.get_case_by_enrolment_code")
    @patch("frontstage.controllers.iac_controller.get_iac_from_enrolment")
    @patch("frontstage.common.cryptographer.Cryptographer.decrypt")
    def test_add_survey_submit_already_enrolled(
        self,
        mock_request,
        decrypt_enrolment_code,
        get_iac_from_enrolment_code,
        get_case_by_enrolment,
        get_collection_exercise,
        get_party_by_business_id,
        *_,
    ):
        mock_request.get(url_banner_api, status_code=404)
        decrypt_enrolment_code.return_value = enrolment_code.encode()
        get_iac_from_enrolment_code.return_value = active_iac
        get_case_by_enrolment.return_value = case_diff_surveyId
        get_collection_exercise.return_value = collection_exercise
        get_party_by_business_id.return_value = business_party

        response = self.app.get(
            f"/surveys/add-survey/add-survey-submit?encrypted_enrolment_code={encrypted_enrolment_code}"
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue("/surveys/todo".encode() in response.data)
        self.assertTrue(case["partyId"].encode() in response.data)
        self.assertTrue(collection_exercise["surveyId"].encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.iac_controller.get_iac_from_enrolment")
    @patch("frontstage.common.cryptographer.Cryptographer.decrypt")
    def test_add_survey_submit_fail(self, mock_request, decrypt_enrolment_code, get_iac_from_enrolment):
        mock_request.get(url_banner_api, status_code=404)
        decrypt_enrolment_code.return_value = enrolment_code.encode()

        error_response = Response()
        error_response.status_code = 500
        error_response.url = url_validate_enrolment
        error = ApiError(logger, error_response)
        error.status_code = 500
        get_iac_from_enrolment.side_effect = error

        response = self.app.get(
            f"/surveys/add-survey/add-survey-submit?encrypted_enrolment_code={encrypted_enrolment_code}"
        )

        self.assertEqual(response.status_code, 500)
        self.assertTrue("An error has occurred".encode() in response.data)

    def test_already_enrolled(self):
        with open("tests/test_data/party/business_party.json") as business_json_data:
            data = json.load(business_json_data)
        survey = "cb8accda-6118-4d3b-85a3-149e28960c54"

        party_id = "f956e8ae-6e0f-4414-b0cf-a07c1aa3e37b"

        self.assertTrue(is_respondent_and_business_enrolled(data["associations"], survey, party_id))

    def test_not_already_enrolled(self):
        with open("tests/test_data/party/business_party.json") as business_json_data:
            data = json.load(business_json_data)
        survey = "64ad4018-2ddd-4894-89e7-33f0135887a2"

        party_id = "40ed60a3-2bbb-4f94-8f0d-56890f70865d"

        self.assertFalse(is_respondent_and_business_enrolled(data["associations"], survey, party_id))
