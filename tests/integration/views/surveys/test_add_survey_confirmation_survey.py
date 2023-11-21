import logging
import unittest
from unittest.mock import patch

import requests_mock
from requests.models import Response
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import ApiError
from tests.integration.mocked_services import (
    business_party,
    case,
    collection_exercise,
    encoded_jwt_token,
    encrypted_enrolment_code,
    enrolment_code,
    survey,
    url_banner_api,
    url_get_case,
)

logger = wrap_logger(logging.getLogger(__name__))


@requests_mock.mock()
class TestAddSurveyConfirmation(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie("authorization", "session_key")
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
        }
        self.patcher = patch("redis.StrictRedis.get", return_value=encoded_jwt_token)

        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @patch("frontstage.controllers.survey_controller.get_survey")
    @patch("frontstage.controllers.collection_exercise_controller.get_collection_exercise")
    @patch("frontstage.controllers.party_controller.get_party_by_business_id")
    @patch("frontstage.controllers.case_controller.get_case_by_enrolment_code")
    @patch("frontstage.controllers.iac_controller.validate_enrolment_code")
    @patch("frontstage.common.cryptographer.Cryptographer.decrypt")
    def test_survey_confirm_organisation_success(
        self,
        mock_request,
        decrypt_enrolment_code,
        _,
        get_case_by_enrolment_code,
        get_business_by_party_id,
        get_collection_exercise,
        get_survey,
    ):
        mock_request.get(url_banner_api, status_code=404)
        decrypt_enrolment_code.return_value = enrolment_code.encode()
        get_case_by_enrolment_code.return_value = case
        get_business_by_party_id.return_value = business_party
        get_collection_exercise.return_value = collection_exercise
        get_survey.return_value = survey

        url = f"/surveys/add-survey/confirm-organisation-survey?encrypted_enrolment_code={encrypted_enrolment_code}"
        response = self.app.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(business_party["name"].encode() in response.data)
        self.assertTrue(survey["longName"].encode() in response.data)

    @patch("frontstage.controllers.case_controller.get_case_by_enrolment_code")
    @patch("frontstage.controllers.iac_controller.validate_enrolment_code")
    @patch("frontstage.common.cryptographer.Cryptographer.decrypt")
    def test_survey_confirm_organisation_fail(self, mock_request, decrypt_enrolment_code, _, get_case):
        mock_request.get(url_banner_api, status_code=404)
        decrypt_enrolment_code.return_value = enrolment_code.encode()

        error_response = Response()
        error_response.status_code = 500
        error_response.url = url_get_case
        error = ApiError(logger, error_response)
        error.status_code = 500
        get_case.side_effect = error

        url = f"/surveys/add-survey/confirm-organisation-survey?encrypted_enrolment_code={encrypted_enrolment_code}"
        response = self.app.get(url)

        self.assertEqual(response.status_code, 500)
        self.assertTrue("An error has occurred".encode() in response.data)
