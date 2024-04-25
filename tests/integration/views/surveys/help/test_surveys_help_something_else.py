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


class TestSurveyHelpInfoAboutThisSurvey(unittest.TestCase):
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

    def set_flask_session(self):
        with self.app.session_transaction() as mock_session:
            mock_session["help_survey_ref"] = "074"
            mock_session["help_ru_ref"] = "49900000001F"

    @requests_mock.mock()
    def test_survey_help_info_bricks(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get("/surveys/help", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Help".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("Something else".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_bricks_with_option_select(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {"option": "something-else"}
        response = self.app.post("/surveys/help", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Help with something else".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("My survey is not listed".encode(), response.data)
        self.assertIn("Something else".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_bricks_with_sub_option_my_survey_is_not_listed(
        self, mock_request, get_survey, get_business
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {"option": "my-survey-is-not-listed"}
        response = self.app.post(
            "/surveys/help/something-else?survey_id=1&business_id=1&ce_id=1&survey_name=4",
            data=form,
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("My survey is not listed".encode(), response.data)
        self.assertIn("When you are selected to return a survey we send an enrolment letter ".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_bricks_with_no_option_select(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {}
        response = self.app.post("/surveys/help/something-else", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Error: ".encode(), response.data)
        self.assertIn('<span class="ons-panel__assistive-text ons-u-vh">Error: </span>'.encode(), response.data)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("You need to choose an option".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_bricks_with_sub_option_something_else(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {"option": "something-else"}
        response = self.app.post("/surveys/help/something-else", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Describe your issue and we will get back to you.".encode(), response.data)
        self.assertIn("Something else".encode(), response.data)
        self.assertIn("Enter message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_send_message_info_bricks_with_sub_option_my_survey_is_not_listed(
        self, mock_request, get_survey, get_business
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        response = self.app.get(
            "/surveys/help/something-else/my-survey-is-not-listed/send-message", follow_redirects=True
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
    @patch("frontstage.views.surveys.help.surveys_help.send_message")
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_create_message_post_success(
        self, mock_request, get_survey, get_business, send_message, get_survey_list, get_respondent_party_by_id
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        send_message.return_value = "a5e67f8a-0d90-4d60-a15a-7e334c75402b"
        get_business.return_value = business_party
        get_survey_list.return_value = survey_list_todo
        get_respondent_party_by_id.return_value = respondent_party
        form = {"body": "info-something-else"}
        response = self.app.post(
            "/surveys/help/something-else/my-survey-is-not-listed/send-message",
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
    def test_create_message_post_something_else_failure(
        self, mock_request, get_survey, get_business, send_message, get_survey_list
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {"body": ""}
        response = self.app.post(
            "/surveys/help/something-else/something-else/send-message",
            data=form,
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Error: ".encode(), response.data)
        self.assertIn('<span class="ons-panel__assistive-text ons-u-vh">Error: </span>'.encode(), response.data)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("Message is required".encode(), response.data)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Describe your issue and we will get back to you.".encode(), response.data)
        self.assertIn("Something else".encode(), response.data)
