import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from tests.integration.mocked_services import (
    business_party,
    encoded_jwt_token,
    survey,
    survey_eq,
    survey_list_todo,
    survey_rsi,
    url_banner_api,
)


class TestSurveyHelpInfoAboutThisSurvey(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie("localhost", "authorization", "session_key")
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
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_bricks(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey_eq
        get_business.return_value = business_party
        response = self.app.get("/surveys/help/074/49900000001F")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Help".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("Information about the ONS".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_bricks_with_no_option_select(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {}
        response = self.app.post("/surveys/help/074/49900000001F", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("You need to choose an option".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_bricks_with_option_select(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {"option": "info-about-the-ons"}
        response = self.app.post("/surveys/help/074/49900000001F", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Information about the ONS".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("Who is the ONS?".encode(), response.data)
        self.assertIn("How safe is my data?".encode(), response.data)
        self.assertIn("Something else".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_bricks_with_sub_option_who_is_the_ons(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {"option": "who-is-the-ons"}
        response = self.app.post("/surveys/help/074/49900000001F/info-about-the-ons", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Who is the ONS?".encode(), response.data)
        self.assertIn("We are the UK’s largest independent producer of official statistics ".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_rsi_with_sub_option_how_safe_is_my_data(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey_rsi
        get_business.return_value = business_party
        form = {"option": "how-safe-is-my-data"}
        response = self.app.post("/surveys/help/023/49900000001F/info-about-the-ons", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("How safe is my data?".encode(), response.data)
        self.assertIn(
            "We uphold our legal obligation to protect data in both the staff we employ, their training, "
            "the procedures we adopt and the IT equipment we use.".encode(),
            response.data,
        )
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_bricks_with_sub_option_something_else(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {"option": "something-else"}
        response = self.app.post("/surveys/help/074/49900000001F/info-about-the-ons", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Describe your issue and we will get back to you.".encode(), response.data)
        self.assertIn("Information about the ONS".encode(), response.data)
        self.assertIn("Enter message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_send_message_info_bricks_with_sub_option_who_is_the_ons(
        self, mock_request, get_survey, get_business
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        response = self.app.get(
            "/surveys/help/074/49900000001F/info-about-the-ons/who-is-the-ons/send-message", follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Describe your issue and we will get back to you.".encode(), response.data)
        self.assertIn("Who is the ONS?".encode(), response.data)
        self.assertIn("Enter message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_send_message_info_bricks_with_sub_option_how_safe_is_my_data(
        self, mock_request, get_survey, get_business
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        response = self.app.get(
            "/surveys/help/074/49900000001F/info-about-the-ons/how-safe-is-my-data/send-message",
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Describe your issue and we will get back to you.".encode(), response.data)
        self.assertIn("How safe is my data?".encode(), response.data)
        self.assertIn("Enter message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_survey_list_details_for_party")
    @patch("frontstage.controllers.conversation_controller.send_message")
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_create_message_post_success(self, mock_request, get_survey, get_business, send_message, get_survey_list):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        get_survey_list.return_value = survey_list_todo
        form = {"body": "info-something-else"}
        response = self.app.post(
            "/surveys/help/074/49900000001F/"
            "send-message?subject=Who is the ONS"
            "&option=info-about-the-ons&sub_option=who-is-the-ons",
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
            "/surveys/help/074/49900000001F/send-message?short_name=Bricks&subject=Information+about+the+ONS"
            "&option=info-about-the-ons&sub_option=not_defined",
            data=form,
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("Message is required".encode(), response.data)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Describe your issue and we will get back to you.".encode(), response.data)
        self.assertIn("Information about the ONS".encode(), response.data)
