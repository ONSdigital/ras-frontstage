import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from tests.integration.mocked_services import (
    business_party,
    encoded_jwt_token,
    respondent_party,
    survey,
    survey_list_todo,
    url_banner_api,
)


class TestTechnicalHelpSurveyNotListed(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie("authorization", "session_key")
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2Vy"
            "X3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"
            # NOQA
        }
        self.patcher = patch("redis.StrictRedis.get", return_value=encoded_jwt_token)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @requests_mock.mock()
    def test_get_technical_message_page_option(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get("/surveys/technical/my-survey-is-not-listed", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("My survey is not listed".encode(), response.data)
        self.assertIn(
            "When you are selected to return a survey we send an enrolment letter to your business's postal "
            "address".encode(),
            response.data,
        )
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    def test_get_technical_message_page_fail(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get("/surveys/technical/my-survey-is-not", follow_redirects=True)
        self.assertEqual(response.status_code, 500)
        self.assertIn("An error has occurred".encode(), response.data)

    @requests_mock.mock()
    def test_get_send_message_page_technical(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.post(
            "/surveys/technical/send-message?option=my-survey-is-not-listed", follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Describe your issue and we will get back to you.".encode(), response.data)
        self.assertIn("My survey is not listed".encode(), response.data)
        self.assertIn("Enter message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    @patch("frontstage.controllers.party_controller.get_survey_list_details_for_party")
    @patch("frontstage.controllers.conversation_controller.send_message")
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_create_message_page_technical_success(
        self, mock_request, get_survey, get_business, send_message, get_survey_list, get_respondent_party_by_id
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_business.return_value = respondent_party
        get_survey_list.return_value = survey_list_todo
        form = {"body": "My survey is not listed"}
        response = self.app.post(
            "/surveys/technical/send-message?option=my-survey-is-not-listed",
            data=form,
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Message sent.".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_survey_list_details_for_party")
    @patch("frontstage.controllers.conversation_controller.send_message")
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_create_message_page_technical_fail(
        self, mock_request, get_survey, get_business, send_message, get_survey_list
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {"body": ""}
        response = self.app.post(
            "/surveys/technical/send-message?option=my-survey-is-not-listed",
            data=form,
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("Message is required".encode(), response.data)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Describe your issue and we will get back to you.".encode(), response.data)
        self.assertIn("My survey is not listed".encode(), response.data)
