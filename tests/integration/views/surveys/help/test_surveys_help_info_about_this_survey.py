import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from tests.integration.mocked_services import encoded_jwt_token, survey_eq, survey, survey_list_todo, url_banner_api, \
    survey_rsi, business_party


class TestSurveyHelpInfoAboutThisSurvey(unittest.TestCase):
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
    def test_survey_help_info_qbs(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey_eq
        get_business.return_value = business_party
        response = self.app.get('/surveys/help/139/49900000001F')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Help".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("Information about the Quarterly Business Survey".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_info_bricks(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        response = self.app.get('/surveys/help/074/49900000001F')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Help".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("Information about the Monthly Survey of Building Materials Bricks".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)
        self.assertIn("Help".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_info_bricks_with_no_option_select(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {
        }
        response = self.app.post('/surveys/help/074/49900000001F',
                                 data=form,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("You need to choose an option".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_info_bricks_with_option_select(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {
            "option": "info-about-this-survey"
        }
        response = self.app.post('/surveys/help/074/49900000001F',
                                 data=form,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Information about the Monthly Survey of Building Materials Bricks".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("Can I be exempt from completing the survey questionnaire?".encode(), response.data)
        self.assertIn("How was my business selected?".encode(), response.data)
        self.assertIn("How long will it take to complete?".encode(), response.data)
        self.assertIn("How long will my business be selected for?".encode(), response.data)
        self.assertIn("Something else".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_info_bricks_with_sub_option_exemption_completing_survey(self, mock_request, get_survey,
                                                                                 get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {
            "option": "exemption-completing-survey"
        }
        response = self.app.post(
            '/surveys/help/074/49900000001F/info-about-this-survey',
            data=form,
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Can I be exempt from completing the survey questionnaire?".encode(), response.data)
        self.assertIn("While this survey is voluntary, we have selected your company in the same way we ".encode(), response.data)
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_info_rsi_with_sub_option_exemption_completing_survey(self, mock_request, get_survey,
                                                                              get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey_rsi
        get_business.return_value = business_party
        form = {
            "option": "exemption-completing-survey"
        }
        response = self.app.post(
            '/surveys/help/023/49900000001F/info-about-this-survey',
            data=form,
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Can I be exempt from completing the survey questionnaire?".encode(), response.data)
        self.assertIn("No. Once selected, the law obliges a business to complete the survey under the provisions "
                      "of the Statistics of Trade Act 1947".encode(), response.data)
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_info_bricks_with_sub_option_why_selected(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {
            "option": "why-selected"
        }
        response = self.app.post(
            '/surveys/help/074/49900000001F/info-about-this-survey',
            data=form,
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("How was my business selected?".encode(), response.data)
        self.assertIn("We select businesses from the Inter-Departmental Business Register (IDBR). ".encode(), response.data)
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_info_bricks_with_sub_option_time_to_complete(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {
            "option": "time-to-complete"
        }
        response = self.app.post(
            '/surveys/help/074/49900000001F/info-about-this-survey',
            data=form,
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("How long will it take to complete?".encode(), response.data)
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_info_bricks_with_sub_option_how_long_selected_for(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {
            "option": "how-long-selected-for"
        }
        response = self.app.post(
            '/surveys/help/074/49900000001F/info-about-this-survey',
            data=form,
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("How long will my business be selected for?".encode(), response.data)
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_info_bricks_with_sub_option_penalties(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {
            "option": "penalties"
        }
        response = self.app.post(
            '/surveys/help/074/49900000001F/info-about-this-survey',
            data=form,
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("What are the penalties for not completing a survey?".encode(), response.data)
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_info_bricks_with_sub_option_something_else(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {
            "option": "info-something-else"
        }
        response = self.app.post(
            '/surveys/help/074/49900000001F/info-about-this-survey',
            data=form,
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Information about the Monthly Survey of Building Materials Bricks".encode(), response.data)
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_send_message_info_bricks_with_sub_option_exemption_completing_survey(self,
                                                                                              mock_request,
                                                                                              get_survey,
                                                                                              get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        response = self.app.get(
            '/surveys/help/074/49900000001F/info-about-this-survey/'
            'exemption-completing-survey/send-message',
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Can I be exempt from completing the survey questionnaire?".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_send_message_info_bricks_with_sub_option_why_selected_survey(self,
                                                                                      mock_request,
                                                                                      get_survey,
                                                                                      get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        response = self.app.get(
            '/surveys/help/074/49900000001F/info-about-this-survey/'
            'why-selected/send-message',
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("How  was my business selected?".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_send_message_info_bricks_with_sub_option_time_to_complete(self,
                                                                                   mock_request,
                                                                                   get_survey,
                                                                                   get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        response = self.app.get(
            '/surveys/help/074/49900000001F/info-about-this-survey/'
            'time-to-complete/send-message',
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("How long will it take to complete?".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_send_message_info_bricks_with_sub_option_how_long_selected_for(self,
                                                                                        mock_request,
                                                                                        get_survey,
                                                                                        get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        response = self.app.get(
            '/surveys/help/074/49900000001F/info-about-this-survey/'
            'how-long-selected-for/send-message',
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Describe your issue and we will get back to you.".encode(), response.data)
        self.assertIn("How long will my business be selected for?".encode(), response.data)
        self.assertIn("Enter message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_send_message_info_bricks_with_sub_option_penalties(self,
                                                                            mock_request,
                                                                            get_survey,
                                                                            get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        response = self.app.get(
            '/surveys/help/B074/49900000001F/info-about-this-survey/'
            'penalties/send-message',
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Describe your issue and we will get back to you.".encode(), response.data)
        self.assertIn("What are the penalties for not completing a survey?".encode(), response.data)
        self.assertIn("Enter message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_send_message_info_bricks_with_sub_option_info_something_else(self,
                                                                                      mock_request,
                                                                                      get_survey,
                                                                                      get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        response = self.app.get(
            '/surveys/help/074/49900000001F/info-about-this-survey/'
            'info-something-else/send-message',
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Describe your issue and we will get back to you.".encode(), response.data)
        self.assertIn("Information about this survey".encode(), response.data)
        self.assertIn("Enter message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.party_controller.get_survey_list_details_for_party')
    @patch("frontstage.controllers.conversation_controller.send_message")
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_create_message_post_success(self, mock_request, get_survey, get_business, get_survey_list):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        get_survey_list.return_value = survey_list_todo
        form = {
            "body": "info-something-else"
        }
        response = self.app.post("/surveys/help/074/49900000001F/"
                                 "send-message?subject=Information about this survey"
                                 "&option=info-about-this-survey&sub_option=info-something-else",
                                 data=form,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Message sent.".encode(), response.data)
