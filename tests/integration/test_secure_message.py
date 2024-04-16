import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from frontstage.exceptions.exceptions import IncorrectAccountAccessError
from tests.integration.mocked_services import (
    encoded_jwt_token,
    message_json,
    url_banner_api,
    url_get_conversation_count,
    url_get_survey_long_name,
    url_get_thread,
)


def create_api_error(status_code, data=None):
    error_json = {"error": {"status_code": status_code, "data": data}}
    return error_json


class TestSecureMessage(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.app.set_cookie("authorization", "session_key")
        self.patcher = patch("redis.StrictRedis.get", return_value=encoded_jwt_token)
        self.patcher.start()
        self.message_form = {
            "subject": "subject",
            "body": "body",
            "send": "Send",
            "thread_id": "7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb",
        }
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
        }

    def tearDown(self):
        self.patcher.stop()

    @requests_mock.mock()
    def test_get_thread_success(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_thread, json={"messages": [message_json], "is_closed": False})
        mock_request.get(url_get_conversation_count, json={"total": 0})
        mock_request.get(
            url_get_survey_long_name,
            json={
                "id": "02b9c366-7397-42f7-942a-76dc5876d86d",
                "shortName": "QBS",
                "longName": "Quarterly Business Survey",
                "surveyRef": "139",
                "legalBasis": "Statistics of Trade Act 1947",
                "surveyType": "Business",
                "surveyMode": "EQ",
                "legalBasisRef": "STA1947",
            },
        )

        response = self.app.get(
            "secure-message/threads/9e3465c0-9172-4974-a7d1-3a01592d1594", headers=self.headers, follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Peter Griffin".encode() in response.data)
        self.assertTrue("testy2".encode() in response.data)
        self.assertTrue("something else".encode() in response.data)
        self.assertTrue("Quarterly Business Survey".encode() in response.data)
        self.assertTrue("OFFICE FOR NATIONAL STATISTICS".encode() in response.data)
        self.assertIn("You can now make changes to your name".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.conversation_controller.try_message_count_from_session")
    def test_get_thread_failure(self, mock_request, message_count):
        mock_request.get(url_banner_api, status_code=404)
        message_count.return_value = 0
        message_json_copy = message_json.copy()
        del message_json_copy["@business_details"]
        mock_request.get(url_get_thread, json={"messages": [message_json_copy]})

        response = self.app.get(
            "secure-message/threads/9e3465c0-9172-4974-a7d1-3a01592d1594", headers=self.headers, follow_redirects=True
        )
        self.assertEqual(response.status_code, 500)

    @requests_mock.mock()
    @patch("frontstage.controllers.conversation_controller.try_message_count_from_session")
    def test_get_thread_wrong_account(self, mock_request, message_count):
        mock_request.get(url_banner_api, status_code=404)
        message_count.return_value = 0
        mock_request.get(url_get_thread, status_code=404, json={"messages": [message_json], "is_closed": False})

        self.assertRaises(IncorrectAccountAccessError)

    @requests_mock.mock()
    @patch("frontstage.controllers.conversation_controller._create_get_conversation_headers")
    @patch("frontstage.controllers.conversation_controller.try_message_count_from_session")
    def test_secure_message_unauthorized_return(self, mock_request, authorization, message_count):
        mock_request.get(url_banner_api, status_code=404)
        message_count.return_value = 0
        authorization.return_value = {"Authorization": "wrong authorization"}

        mock_request.get(url_get_thread, status_code=403)

        response = self.app.get(
            "secure-message/threads/9e3465c0-9172-4974-a7d1-3a01592d1594", headers=self.headers, follow_redirects=True
        )
        self.assertTrue("The page you are trying to view is not for this account.".encode() in response.data)
