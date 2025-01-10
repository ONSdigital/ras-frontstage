import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from frontstage.controllers.conversation_controller import InvalidSecureMessagingForm
from tests.integration.mocked_services import encoded_jwt_token, url_banner_api


class TestCookiesContact(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie("authorization", "session_key")
        self.patcher = patch("redis.StrictRedis.get", return_value=encoded_jwt_token)
        self.patcher.start()
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
        }

    @requests_mock.mock()
    def test_cookies_success(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get("/cookies")

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Cookies on surveys.ons.gov.uk".encode() in response.data)
        self.assertTrue(
            "Cookies are small files saved on your phone, tablet or computer when you visit a website".encode()
            in response.data
        )

    @requests_mock.mock()
    def test_privacy_success(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get("/privacy-and-data-protection")

        self.assertEqual(response.status_code, 200)
        self.assertTrue("We will keep your information secure and confidential".encode() in response.data)
        self.assertTrue("Where can I find out more about how my information will be treated?".encode() in response.data)

    @requests_mock.mock()
    def test_contact_success(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get("/contact-us")

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Contact us".encode() in response.data)
        self.assertTrue("Opening hours:".encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.views.contact_us.secure_message_enrolment_options")
    def test_secure_message_form(self, mock_request, secure_message_enrolment_options):
        mock_request.get(url_banner_api, status_code=404)
        secure_message_enrolment_options.return_value = {
            "survey": [
                {
                    "value": "41320b22-b425-4fba-a90e-718898f718ce",
                    "text": "Annual Inward Foreign Direct Investment Survey",
                },
            ],
            "subject": [
                {"value": "Technical difficulties", "text": "Technical difficulties"},
            ],
        }
        response = self.app.get("/contact-us/send-message")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Annual Inward Foreign Direct Investment Survey".encode() in response.data)
        self.assertTrue("Technical difficulties".encode() in response.data)
        self.assertTrue("Your personal information is protected by law".encode() in response.data)
        self.assertTrue('input type="hidden" name="business_id"'.encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.views.contact_us.secure_message_enrolment_options")
    def test_secure_message_form_multiple_businesses(self, mock_request, secure_message_enrolment_options):
        mock_request.get(url_banner_api, status_code=404)
        secure_message_enrolment_options.return_value = {
            "survey": [],
            "subject": [],
            "business": [
                {"value": "aebee450-46da-4f8b-a7a6-d4632087f2a3", "text": "Test Business 2"},
                {"value": "bebee450-46da-4f8b-a7a6-d4632087f2a3", "text": "Test Business 1"},
            ],
        }

        response = self.app.get("/contact-us/send-message")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Test Business 1".encode() in response.data)
        self.assertTrue("Test Business 2".encode() in response.data)
        self.assertFalse('input type="hidden" name="business_id"'.encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.views.contact_us.secure_message_enrolment_options")
    @patch("frontstage.views.contact_us.send_secure_message")
    def test_invalid_secure_message_form(self, mock_request, send_secure_message, secure_message_enrolment_options):
        secure_message_enrolment_options.return_value = {}
        mock_request.get(url_banner_api, status_code=404)
        send_secure_message.side_effect = InvalidSecureMessagingForm({"body": ["Message is required"]})

        response = self.app.post("/contact-us/send-message")

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Message is required".encode() in response.data)
