import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from tests.integration.mocked_services import encoded_jwt_token, respondent_party, survey_eq, survey, \
    survey_list_todo, url_banner_api, url_get_respondent_party


class TestSurveyHelpWithThisSurvey(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie('localhost', 'authorization', 'session_key')
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"
            # NOQA
        }
        self.patcher = patch('redis.StrictRedis.get', return_value=encoded_jwt_token)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_for_qbs(self, mock_request, get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey_eq
        response = self.app.get('/surveys/help/QBS/7f9d681b-419c-4919-ba41-03fde7dc40f7')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Help".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("Help completing the Quarterly Business Survey".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_for_bricks(self, mock_request, get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        response = self.app.get('/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Help".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("Help completing the Monthly Survey of Building Materials Bricks".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_for_bricks_with_option_select(self, mock_request, get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        form = {
            "option": "help-completing-this-survey"
        }
        response = self.app.post('/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7',
                                 data=form,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Help completing the Monthly Survey of Building Materials Bricks".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("I need help answering a survey question".encode(), response.data)
        self.assertIn("I do not have specific figures for a response".encode(), response.data)
        self.assertIn("Something else".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_for_bricks_with_sub_option_answer_a_survey_question(self, mock_request, get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        form = {
            "option": "answer-survey-question"
        }
        response = self.app.post(
            '/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/help-completing-this-survey',
            data=form,
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Send us a message with a description of your issue".encode(), response.data)
        self.assertIn("Help answering a survey question".encode(), response.data)
        self.assertIn("Create message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_for_bricks_with_sub_option_specific_figures_for_a_response(self, mock_request, get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        form = {
            "option": "do-not-have-specific-figures"
        }
        response = self.app.post(
            '/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/help-completing-this-survey',
            data=form,
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("I do not have specific figures for a response".encode(), response.data)
        self.assertIn(
            "We do not expect you to spend too long or go to any great expense to get hold of the information we request.".encode(),
            response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_get_send_help_message_page_for_bricks_with_sub_option_specific_figures_for_a_response(self,
                                                                                                   mock_request,
                                                                                                   get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        response = self.app.get(
            '/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/help-completing-this-survey/'
            'do-not-have-specific-figures/send-message')

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Send us a message with a description of your issue".encode(), response.data)
        self.assertIn("I don’t have specific figures for a response".encode(), response.data)
        self.assertIn("Create message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_for_bricks_with_sub_option_unable_to_return_by_deadline(self, mock_request, get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        form = {
            "option": "unable-to-return-by-deadline"
        }
        response = self.app.post(
            '/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/help-completing-this-survey',
            data=form,
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("I am unable to return the data by the deadline".encode(), response.data)
        self.assertIn(
            "All business surveys have a deadline by which you must submit data for us to use "
            "for statistical purposes.".encode(),
            response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_get_send_help_message_page_for_bricks_with_sub_option_specific_figures_for_a_response(self, mock_request,
                                                                                                   get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        response = self.app.get(
            '/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/help-completing-this-survey/'
            'unable-to-return-by-deadline/send-message')

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Send us a message with a description of your issue".encode(), response.data)
        self.assertIn("I’m unable to return the data by the deadline".encode(), response.data)
        self.assertIn("Create message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_for_bricks_with_sub_option_something_else(self, mock_request, get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        form = {
            "option": "something-else"
        }
        response = self.app.post(
            '/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/help-completing-this-survey',
            data=form,
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Send us a message with a description of your issue".encode(), response.data)
        self.assertIn("Help completing this survey".encode(), response.data)
        self.assertIn("Create message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.party_controller.get_survey_list_details_for_party')
    @patch("frontstage.controllers.conversation_controller.send_message")
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_create_message_post_success(self, mock_request, get_survey, send_message, get_survey_list):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_survey_list.return_value = survey_list_todo
        form = {
            "body": "something-else"
        }
        response = self.app.post("/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/"
                                 "send-message?subject=Help completing this survey"
                                 "&option=help-completing-this-survey&sub_option=answer-survey-question",
                                 data=form,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Message sent.".encode(), response.data)

    @requests_mock.mock()
    def test_account_help_redirects_correctly(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, json=respondent_party, status_code=200)

        form = {
            'option': 'help-with-my-account'
        }
        response = self.app.post('/surveys/help/QBS/33524ade-c5d4-4017-aced-2ad25b397072',
                                 data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Account details'.encode(), response.data)
        self.assertIn('Change my contact details'.encode(), response.data)
