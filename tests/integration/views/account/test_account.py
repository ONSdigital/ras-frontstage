import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from tests.integration.mocked_services import (
    encoded_jwt_token,
    respondent_enrolments,
    respondent_party,
    survey_list_todo,
    url_banner_api,
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

    def tearDown(self):
        self.patcher.stop()

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    def test_account(self, mock_request, get_respondent_party_by_id):
        mock_request.get(url_banner_api, status_code=404)
        get_respondent_party_by_id.return_value = respondent_party
        with app.app_context():
            response = self.app.get("/my-account")

            self.assertEqual(response.status_code, 200)
            self.assertTrue("example@example.com".encode() in response.data)
            self.assertTrue("0987654321".encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    def test_account_options(self, mock_request, get_respondent_party_by_id):
        mock_request.get(url_banner_api, status_code=404)
        get_respondent_party_by_id.return_value = respondent_party
        with app.app_context():
            response = self.app.get("/my-account")

            self.assertEqual(response.status_code, 200)
            self.assertIn(b"example@example.com", response.data)
            self.assertIn(b"My Account", response.data)
            self.assertIn(b"<a href='/my-account/change-account-details'>Edit contact details</a>", response.data)
            self.assertIn(b"<a href='/my-account/change-password'>Change password</a>", response.data)
            self.assertIn(b"I want to delete my account", response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    def test_account_options_selection(self, mock_request, get_respondent_party_by_id):
        mock_request.get(url_banner_api, status_code=404)
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post("/my-account", data=self.contact_details_form, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Phone number".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    def test_account_contact_details_error(self, mock_request, get_respondent_party_by_id):
        mock_request.get(url_banner_api, status_code=404)
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post("/my-account/change-account-details", data={"first_name": ""}, follow_redirects=True)

        self.assertIn("There is a problem with your answer".encode(), response.data)
        self.assertIn("Enter your first name".encode(), response.data)
        self.assertIn("Enter your last name".encode(), response.data)
        self.assertIn("Enter an email address".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    @patch("frontstage.controllers.party_controller.update_account")
    @patch("frontstage.controllers.party_controller.get_case_list_for_respondent")
    def test_account_change_account_email_address(
        self, mock_request, get_survey_list, update_account, get_respondent_party_by_id
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_respondent_party_by_id.return_value = respondent_party
        get_survey_list.return_value = survey_list_todo
        response = self.app.post(
            "/my-account/change-account-details",
            data={
                "first_name": "test account",
                "last_name": "test_account",
                "phone_number": "07772257773",
                "email_address": "exampleone@example.com",
                "confirm_email_address": "exampleone@example.com",
            },
            follow_redirects=True,
        )
        self.assertIn("We have sent you an email to confirm your new email address.".encode(), response.data)
        self.assertIn("Your contact details have changed".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    def test_account_options_selection_change_password(self, mock_request, get_respondent_party_by_id):
        mock_request.get(url_banner_api, status_code=404)
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post("/my-account", data={"option": "change_password"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Change your password".encode() in response.data)
        self.assertTrue("Enter your current password".encode() in response.data)
        self.assertTrue("Your password must have:".encode() in response.data)
        self.assertTrue("at least 12 characters".encode() in response.data)
        self.assertTrue("at least 1 uppercase letter".encode() in response.data)
        self.assertTrue("at least 1 symbol (eg: ?!£%)".encode() in response.data)
        self.assertTrue("at least 1 number".encode() in response.data)
        self.assertTrue("New Password".encode() in response.data)
        self.assertTrue("Re-type your new password".encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    def test_share_survey_options_selection(self, mock_request, get_respondent_party_by_id):
        mock_request.get(url_banner_api, status_code=404)
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post("/my-account", data={"option": "share_surveys"}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Share access to your surveys".encode() in response.data)
        self.assertTrue("What will happen".encode() in response.data)
        self.assertTrue("Select which surveys you want to share.".encode() in response.data)
        self.assertTrue(
            "Enter the email address of the person who will be responding to these surveys.".encode() in response.data
        )
        self.assertTrue("We will email them the instructions to access the surveys.".encode() in response.data)
        self.assertTrue(
            "Once we confirm their access, they will be able to respond to surveys on your behalf and "
            "share access with colleagues.".encode() in response.data
        )
        self.assertTrue("Continue".encode() in response.data)
        self.assertTrue("Cancel".encode() in response.data)
