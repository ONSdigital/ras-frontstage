import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from tests.integration.mocked_services import (
    encoded_jwt_token,
    respondent_party,
    url_auth_token,
    url_banner_api,
    url_password_change,
)


class TestSurveyList(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie("authorization", "session_key")
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2Vy"
            "X3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"
            # NOQA
        }
        self.patcher = patch("redis.StrictRedis.get", return_value=encoded_jwt_token)
        self.contact_details_form = {"option": "contact_details"}
        self.patcher.start()
        self.auth_error = {"detail": "Unauthorized user credentials"}

    def tearDown(self):
        self.patcher.stop()

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    @patch("frontstage.controllers.party_controller.get_survey_list_details_for_party")
    def test_account_password_change_success(self, mock_request, get_survey_list, get_respondent_party_by_id):
        survey_list = [
            {
                "case_id": "6f698975-0a36-45ff-ba66-7a575e414023",
                "status": "Not started",
                "collection_instrument_type": "EQ",
                "survey_id": "02b9c366-7397-42f7-942a-76dc5876d86d",
                "survey_long_name": "Quarterly Business Survey",
                "survey_short_name": "QBS",
                "survey_ref": "139",
                "business_party_id": "44d8db36-2319-41c6-8887-79033ce55a4b",
                "business_name": "PC UNIVERSE",
                "trading_as": "PC LTD",
                "business_ref": "49900000007",
                "period": "December 2019",
                "submit_by": "26 Mar 2021",
                "collection_exercise_ref": "1912",
                "added_survey": None,
                "display_button": True,
            }
        ]
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_auth_token, status_code=204)
        mock_request.put(url_password_change, status_code=200)
        get_respondent_party_by_id.return_value = respondent_party
        get_survey_list.return_value = survey_list
        response = self.app.post(
            "/my-account/change-password",
            data={"password": "test", "new_password": "Password123!", "new_password_confirm": "Password123!"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            "Your password has been changed. Please login with your new password.".encode() in response.data
        )
        self.assertTrue("Sign in".encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    def test_account_password_change_form_validation_errors_does_not_meet_requirement(
        self, mock_request, get_respondent_party_by_id
    ):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_auth_token, status_code=204)
        mock_request.put(url_password_change, status_code=200)
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post(
            "/my-account/change-password",
            data={"password": "test", "new_password": "Password123", "new_password_confirm": "Password123"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Your password doesn't meet the requirements".encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    def test_account_password_change_validation_error(self, mock_request, get_respondent_party_by_id):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_auth_token, status_code=204)
        mock_request.put(url_password_change, status_code=200)
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post("/my-account/change-password", data={}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("There are 2 errors on this page".encode() in response.data)
        self.assertTrue("Your current password is required".encode() in response.data)
        self.assertTrue("Your new password is required".encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    def test_account_password_change_validation_error_old_password_incorrect(
        self, mock_request, get_respondent_party_by_id
    ):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_auth_token, status_code=401, json=self.auth_error)
        mock_request.put(url_password_change, status_code=200)
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post(
            "/my-account/change-password",
            data={"password": "test", "new_password": "Password123!", "new_password_confirm": "Password123!"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue("There is 1 error on this page".encode() in response.data)
        self.assertTrue("Incorrect current password".encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    def test_account_password_change_validation_error_old_new_password_same(
        self, mock_request, get_respondent_party_by_id
    ):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_auth_token, status_code=401, json=self.auth_error)
        mock_request.put(url_password_change, status_code=200)
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post(
            "/my-account/change-password",
            data={"password": "Password123!", "new_password": "Password123!", "new_password_confirm": "Password123!"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue("There is 1 error on this page".encode() in response.data)
        self.assertTrue("Your new password is the same as your old password".encode() in response.data)
