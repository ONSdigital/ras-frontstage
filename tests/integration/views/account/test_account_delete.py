import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from tests.integration.mocked_services import (
    encoded_jwt_token,
    respondent_party,
    url_auth_delete,
    url_banner_api,
)


class TestAccountDelete(unittest.TestCase):
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
    def test_account_delete(self, mock_request, get_respondent_party_by_id):
        mock_request.get(url_banner_api, status_code=404)
        get_respondent_party_by_id.return_value = {
            "associations": [],
            "emailAddress": "example@example.com",
            "firstName": "first_name",
            "id": "f956e8ae-6e0f-4414-b0cf-a07c1aa3e37b",
            "lastName": "last_name",
            "sampleUnitType": "BI",
            "status": "ACTIVE",
            "telephone": "0987654321",
            "respondent_id": 1,
        }
        with app.app_context():
            response = self.app.get("/my-account/delete")

            self.assertEqual(response.status_code, 200)
            self.assertTrue("Delete account".encode() in response.data)
            self.assertTrue("All of the information about your account will be deleted.".encode() in response.data)
            self.assertTrue("Once your data has been removed, it cannot be recovered.".encode() in response.data)
            self.assertTrue(
                "You will not be able to set up a new account until you are selected for a new survey.".encode()
                in response.data
            )

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    def test_account_delete_confirm(self, mock_request, get_respondent_party_by_id):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.delete(url_auth_delete, status_code=204)
        get_respondent_party_by_id.return_value = {
            "associations": [],
            "emailAddress": "example@example.com",
            "firstName": "first_name",
            "id": "f956e8ae-6e0f-4414-b0cf-a07c1aa3e37b",
            "lastName": "last_name",
            "sampleUnitType": "BI",
            "status": "ACTIVE",
            "telephone": "0987654321",
            "respondent_id": 1,
        }
        with app.app_context():
            response = self.app.post("/my-account/delete", follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertTrue("Sign in".encode() in response.data)
            self.assertTrue("New to this service?".encode() in response.data)
            self.assertTrue("Email Address".encode() in response.data)
            self.assertTrue("Password".encode() in response.data)
            self.assertTrue("Forgot password?".encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    def test_account_delete_not_allowed(self, mock_request, get_respondent_party_by_id):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.delete(url_auth_delete, status_code=204)
        get_respondent_party_by_id.return_value = respondent_party
        with app.app_context():
            response = self.app.get("/my-account/delete", follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertTrue("This account can not be deleted.".encode() in response.data)
            self.assertTrue(
                "This operation is not allowed as you are currently assigned to a survey.".encode() in response.data
            )
