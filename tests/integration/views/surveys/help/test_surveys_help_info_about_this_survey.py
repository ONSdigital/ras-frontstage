import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from tests.integration.mocked_services import encoded_jwt_token, survey_eq, survey, survey_list_todo, url_banner_api, \
    survey_rsi


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
    def test_survey_help_info_qbs(self, mock_request, get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey_eq
        response = self.app.get('/surveys/help/QBS/7f9d681b-419c-4919-ba41-03fde7dc40f7')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Help".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("Information about the Quarterly Business Survey".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_info_bricks(self, mock_request, get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        response = self.app.get('/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Help".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("Information about the Monthly Survey of Building Materials Bricks".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)
        self.assertIn("Help".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_info_bricks_with_no_option_select(self, mock_request, get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        form = {
        }
        response = self.app.post('/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7',
                                 data=form,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("You need to choose an option".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_info_bricks_with_option_select(self, mock_request, get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        form = {
            "option": "info-about-this-survey"
        }
        response = self.app.post('/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7',
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
    def test_survey_help_info_bricks_with_sub_option_exemption_completing_survey(self, mock_request, get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        form = {
            "option": "exemption-completing-survey"
        }
        response = self.app.post(
            '/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/info-about-this-survey',
            data=form,
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Can I be exempt from completing the survey questionnaire?".encode(), response.data)
        self.assertIn("Whilst this survey is voluntary, we have selected your company through our normal "
                      "selection processes. This means that any data you submit to us on this subject will "
                      "allow us to produce statistics on things which may not otherwise be asked as part of "
                      "mandatory surveys.".encode(), response.data)
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_info_rsi_with_sub_option_exemption_completing_survey(self, mock_request, get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey_rsi
        form = {
            "option": "exemption-completing-survey"
        }
        response = self.app.post(
            '/surveys/help/RSI/7f9d681b-419c-4919-ba41-03fde7dc40f7/info-about-this-survey',
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
    def test_survey_help_info_bricks_with_sub_option_why_selected(self, mock_request, get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        form = {
            "option": "why-selected"
        }
        response = self.app.post(
            '/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/info-about-this-survey',
            data=form,
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("How was my business selected?".encode(), response.data)
        self.assertIn("We select businesses from the Inter-Departmental Business Register (IDBR). "
                      "The IDBR is a register of businesses in the UK registered for PAYE, VAT or "
                      "with Companies House.".encode(), response.data)
        self.assertIn("Selection depends on several factors. For example, the number of people "
                      "employed, how many other businesses are operating in the same industry "
                      "and the size of those businesses.".encode(), response.data)
        self.assertIn("We always include large businesses in the survey sample because the information "
                      "they provide can be significant.".encode(), response.data)
        self.assertIn("Large businesses are usually defined as having over 100 employees.".encode(), response.data)
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_info_bricks_with_sub_option_time_to_complete(self, mock_request, get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        form = {
            "option": "time-to-complete"
        }
        response = self.app.post(
            '/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/info-about-this-survey',
            data=form,
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("How long will it take to complete?".encode(), response.data)
        self.assertIn("We design each survey to answer a set of statistical requirements. "
                      "The length and volume of questions can vary.".encode(), response.data)
        self.assertIn("The length of time it takes your business to complete will depend on the "
                      "availability of the information requested.".encode(), response.data)
        self.assertIn("We can help with a specific issue by using our secure message service.".encode(), response.data)
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_info_bricks_with_sub_option_how_long_selected_for(self, mock_request, get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        form = {
            "option": "how-long-selected-for"
        }
        response = self.app.post(
            '/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/info-about-this-survey',
            data=form,
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("How long will my business be selected for?".encode(), response.data)
        self.assertIn("We cannot give a definitive period of selection for business surveys as this depends on "
                      "many factors.".encode(), response.data)
        self.assertIn("We choose a specific number of businesses for a survey sample. This can change as "
                      "businesses start and other businesses stop trading. As employment levels within each "
                      "business change, so do the number of businesses in each size-band.".encode(), response.data)
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_info_bricks_with_sub_option_penalties(self, mock_request, get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        form = {
            "option": "penalties"
        }
        response = self.app.post(
            '/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/info-about-this-survey',
            data=form,
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("What happens if I don’t complete a survey?".encode(), response.data)
        self.assertIn("Failure to comply could lead to prosecution at a Magistrates Court with a fine up "
                      "to a maximum of £2,500 (last updated by section 17 of the Criminal Justice Act 1991)."
                      .encode(), response.data)
        self.assertIn("If this happens you will still need to complete the questionnaire.".encode(), response.data)
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_info_bricks_with_sub_option_something_else(self, mock_request, get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        form = {
            "option": "info-something-else"
        }
        response = self.app.post(
            '/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/info-about-this-survey',
            data=form,
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Information about the Monthly Survey of Building Materials Bricks".encode(), response.data)
        self.assertIn("You will find answers to most of your questions in our"
                      .encode(), response.data)
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_send_message_info_bricks_with_sub_option_exemption_completing_survey(self,
                                                                                              mock_request,
                                                                                              get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        response = self.app.get(
            '/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/info-about-this-survey/'
            'exemption-completing-survey/send-message',
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Can I be exempt from completing the survey questionnaire?".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_send_message_info_bricks_with_sub_option_why_selected_survey(self,
                                                                                      mock_request,
                                                                                      get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        response = self.app.get(
            '/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/info-about-this-survey/'
            'why-selected/send-message',
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("How / why was my business selected?".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_send_message_info_bricks_with_sub_option_time_to_complete(self,
                                                                                   mock_request,
                                                                                   get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        response = self.app.get(
            '/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/info-about-this-survey/'
            'time-to-complete/send-message',
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("How long will it take to complete?".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_send_message_info_bricks_with_sub_option_how_long_selected_for(self,
                                                                                        mock_request,
                                                                                        get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        response = self.app.get(
            '/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/info-about-this-survey/'
            'how-long-selected-for/send-message',
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Send us a message with a description of your issue".encode(), response.data)
        self.assertIn("How long will my business be selected for?".encode(), response.data)
        self.assertIn("Create message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_send_message_info_bricks_with_sub_option_penalties(self,
                                                                            mock_request,
                                                                            get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        response = self.app.get(
            '/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/info-about-this-survey/'
            'penalties/send-message',
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Send us a message with a description of your issue".encode(), response.data)
        self.assertIn("What happens if I don’t complete a survey?".encode(), response.data)
        self.assertIn("Create message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.survey_controller.get_survey_by_short_name')
    def test_survey_help_send_message_info_bricks_with_sub_option_info_something_else(self,
                                                                                      mock_request,
                                                                                      get_survey):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        response = self.app.get(
            '/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/info-about-this-survey/'
            'info-something-else/send-message',
            follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Send us a message with a description of your issue".encode(), response.data)
        self.assertIn("Information about this survey".encode(), response.data)
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
            "body": "info-something-else"
        }
        response = self.app.post("/surveys/help/Bricks/7f9d681b-419c-4919-ba41-03fde7dc40f7/"
                                 "send-message?subject=Information about this survey"
                                 "&option=info-about-this-survey&sub_option=info-something-else",
                                 data=form,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Message sent.".encode(), response.data)
