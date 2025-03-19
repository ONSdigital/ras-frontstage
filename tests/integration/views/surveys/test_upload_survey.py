import io
import logging
import unittest
from unittest.mock import patch

import requests_mock
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import CiUploadError
from tests.integration.mocked_services import (
    business_party,
    case,
    collection_exercise,
    encoded_jwt_token,
    survey,
    url_banner_api,
    url_get_business_party,
    url_get_case,
    url_get_survey_by_short_name,
)

logger = wrap_logger(logging.getLogger(__name__))


@requests_mock.mock()
class TestUploadSurvey(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie("authorization", "session_key")
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
        }
        self.survey_file = dict(file=(io.BytesIO(b"my file contents"), "testfile.xlsx"))
        self.patcher = patch("redis.StrictRedis.get", return_value=encoded_jwt_token)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @patch("frontstage.controllers.collection_instrument_controller.upload_collection_instrument")
    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    def test_upload_survey_success(self, mock_request, *_, upload_collection_instrument):
        mock_request.get(
            f"{url_get_business_party}?collection_exercise_id={collection_exercise['id']}&verbose=True",
            json=business_party,
            status_code=200,
        )
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_survey_by_short_name, json=survey, status_code=200)
        mock_request.get(url_get_case, json=case, status_code=200)
        upload_collection_instrument.return_value = None
        self.survey_file = dict(file=(io.BytesIO(b"my file contents"), "testfile.xlsx"))
        response = self.app.post(
            f'/surveys/upload-survey?case_id={case["id"]}&business_party_id={business_party["id"]}'
            f'&survey_short_name={survey["shortName"]}',
            data=self.survey_file,
        )

        self.assertEqual(response.status_code, 200)

    @patch("frontstage.controllers.collection_instrument_controller.upload_collection_instrument")
    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    def test_upload_survey_fail_unexpected_error(self, mock_request, _, upload_ci):
        mock_request.get(
            f"{url_get_business_party}?collection_exercise_id={collection_exercise['id']}&verbose=True",
            json=business_party,
            status_code=200,
        )
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_case, json=case, status_code=200)
        mock_request.get(url_get_survey_by_short_name, json=survey, status_code=200)
        error_message = "fail"
        error = CiUploadError(error_message)
        upload_ci.side_effect = error
        self.survey_file = dict(file=(io.BytesIO(b"my file contents"), "testfile.xlsx"))
        response = self.app.post(
            f'/surveys/upload-survey?case_id={case["id"]}&business_party_id={business_party["id"]}'
            f'&survey_short_name={survey["shortName"]}',
            data=self.survey_file,
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue("/surveys/upload-failed".encode() in response.data)

    @patch("frontstage.controllers.collection_instrument_controller.upload_collection_instrument")
    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    def test_upload_survey_fail_type_error(self, mock_request, _, upload_ci):
        mock_request.get(
            f"{url_get_business_party}?collection_exercise_id={collection_exercise['id']}&verbose=True",
            json=business_party,
            status_code=200,
        )
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_survey_by_short_name, json=survey, status_code=200)
        mock_request.get(url_get_case, json=case, status_code=200)

        error_message = ".xlsx format"
        error = CiUploadError(error_message)
        upload_ci.side_effect = error
        self.survey_file = dict(file=(io.BytesIO(b"my file contents"), "testfile.xlsx"))
        response = self.app.post(
            f'/surveys/upload-survey?case_id={case["id"]}&business_party_id={business_party["id"]}'
            f'&survey_short_name={survey["shortName"]}',
            data=self.survey_file,
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue("/surveys/upload-failed".encode() in response.data)

    @patch("frontstage.controllers.collection_instrument_controller.upload_collection_instrument")
    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    def test_upload_survey_fail_char_limit_error(self, mock_request, _, upload_ci):
        mock_request.get(
            f"{url_get_business_party}?collection_exercise_id={collection_exercise['id']}&verbose=True",
            json=business_party,
            status_code=200,
        )
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_case, json=case, status_code=200)
        mock_request.get(url_get_survey_by_short_name, json=survey, status_code=200)
        error_message = "50 characters"
        error = CiUploadError(error_message)
        upload_ci.side_effect = error
        self.survey_file = dict(file=(io.BytesIO(b"my file contents"), "testfile.xlsx"))
        response = self.app.post(
            f'/surveys/upload-survey?case_id={case["id"]}&business_party_id={business_party["id"]}'
            f'&survey_short_name={survey["shortName"]}',
            data=self.survey_file,
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue("/surveys/upload-failed".encode() in response.data)

    @patch("frontstage.controllers.collection_instrument_controller.upload_collection_instrument")
    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    def test_upload_survey_fail_size_error(self, mock_request, _, upload_ci):
        mock_request.get(
            f"{url_get_business_party}?collection_exercise_id={collection_exercise['id']}&verbose=True",
            json=business_party,
            status_code=200,
        )
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_case, json=case, status_code=200)
        mock_request.get(url_get_survey_by_short_name, json=survey, status_code=200)
        error_message = "File too large"
        error = CiUploadError(error_message)
        upload_ci.side_effect = error

        self.survey_file = dict(file=(io.BytesIO(b"my file contents"), "testfile.xlsx"))
        response = self.app.post(
            f'/surveys/upload-survey?case_id={case["id"]}&business_party_id={business_party["id"]}'
            f'&survey_short_name={survey["shortName"]}',
            data=self.survey_file,
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue("/surveys/upload-failed".encode() in response.data)

    def test_upload_survey_content_too_long(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        file_data = "a" * 21 * 1024 * 1024
        over_size_file = dict(file=(io.BytesIO(file_data.encode()), "testfile.xlsx"))
        response = self.app.post(
            f'/surveys/upload-survey?case_id={case["id"]}&business_party_id={business_party["id"]}'
            f'&survey_short_name={survey["shortName"]}',
            data=over_size_file,
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue("/surveys/upload-failed".encode() in response.data)
