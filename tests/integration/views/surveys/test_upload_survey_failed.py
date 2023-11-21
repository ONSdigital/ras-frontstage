import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from tests.integration.mocked_services import (
    business_party,
    case,
    collection_exercise,
    collection_instrument_seft,
    encoded_jwt_token,
    survey,
    url_banner_api,
)


@requests_mock.mock()
class TestUploadSurveyFailed(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie("authorization", "session_key")
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
        }
        self.patcher = patch("redis.StrictRedis.get", return_value=encoded_jwt_token)
        self.case_data = {
            "collection_exercise": collection_exercise,
            "collection_instrument": collection_instrument_seft,
            "survey": survey,
            "business_party": business_party,
        }
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @patch("frontstage.controllers.case_controller.get_case_data")
    def test_upload_failed_no_error_info(self, mock_request, get_case_data):
        mock_request.get(url_banner_api, status_code=404)
        get_case_data.return_value = self.case_data
        response = self.app.get(
            f'/surveys/upload-failed?case_id={case["id"]}&business_party_id={business_party["id"]}&survey_short_name={survey["shortName"]}'
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Something went wrong".encode() in response.data)
        self.assertTrue("Please try uploading your spreadsheet again".encode() in response.data)

    @patch("frontstage.controllers.case_controller.get_case_data")
    def test_upload_failed_type_error_info(self, mock_request, get_case_data):
        mock_request.get(url_banner_api, status_code=404)
        get_case_data.return_value = self.case_data
        response = self.app.get(
            f'/surveys/upload-failed?case_id={case["id"]}&business_party_id={business_party["id"]}&survey_short_name={survey["shortName"]}'
            f"&error_info=type"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Error uploading - incorrect file type".encode() in response.data)
        self.assertTrue("The spreadsheet must be in .xls or .xlsx format".encode() in response.data)

    @patch("frontstage.controllers.case_controller.get_case_data")
    def test_upload_failed_charLimit_error_info(self, mock_request, get_case_data):
        mock_request.get(url_banner_api, status_code=404)
        get_case_data.return_value = self.case_data
        response = self.app.get(
            f'/surveys/upload-failed?case_id={case["id"]}&business_party_id={business_party["id"]}&survey_short_name={survey["shortName"]}'
            f"&error_info=charLimit"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Error uploading - file name too long".encode() in response.data)
        self.assertTrue(
            "The file name of your spreadsheet must be less than 50 characters long".encode() in response.data
        )

    @patch("frontstage.controllers.case_controller.get_case_data")
    def test_upload_failed_size_error_info(self, mock_request, get_case_data):
        mock_request.get(url_banner_api, status_code=404)
        get_case_data.return_value = self.case_data
        response = self.app.get(
            f'/surveys/upload-failed?case_id={case["id"]}&business_party_id={business_party["id"]}&survey_short_name={survey["shortName"]}'
            f"&error_info=size"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Error uploading - file size too large".encode() in response.data)
        self.assertTrue("The spreadsheet must be smaller than 20MB in size".encode() in response.data)

    def test_upload_survey_failed_with_no_business_party_id_fails(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get(
            f'/surveys/upload-failed?case_id={case["id"]}&survey_short_name={survey["shortName"]}&error_info=size'
        )

        self.assertEqual(response.status_code, 400)

    def test_upload_survey_failed_with_no_survey_short_name_fails(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get(
            f'/surveys/upload-failed?case_id={case["id"]}&business_party_id={business_party["id"]}' f"&error_info=size"
        )

        self.assertEqual(response.status_code, 400)
