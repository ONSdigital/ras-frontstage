import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from tests.integration.mocked_services import (
    encoded_jwt_token,
    respondent_party,
    survey_list_todo,
    url_banner_api,
    url_get_respondent_party,
)


class TestSurveyHelpWithThisSurvey(unittest.TestCase):
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
    def test_survey_help_for_qbs(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get("/surveys/help?survey_name=Quarterly+Business+Survey")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Help".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("Help completing the Quarterly Business Survey".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    def test_survey_help_for_bricks(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get(f"/surveys/help{self._help_details()}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Help".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("Help completing the Monthly Survey of Building Materials Bricks".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    def test_survey_help_for_bricks_with_option_select(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        form = {"option": "help-completing-this-survey"}
        response = self.app.post(f"/surveys/help{self._help_details()}", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Help completing the Monthly Survey of Building Materials Bricks".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("I need help answering a survey question".encode(), response.data)
        self.assertIn("I do not have specific figures for a response".encode(), response.data)
        self.assertIn("Something else".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    def test_survey_help_for_bricks_with_no_option_select(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        form = {"option": ""}
        response = self.app.post(
            f"/surveys/help/help-completing-this-survey{self._help_details()}", data=form, follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Error: ".encode(), response.data)
        self.assertIn('<span class="ons-panel__assistive-text ons-u-vh">Error: </span>'.encode(), response.data)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("You need to choose an option".encode(), response.data)

    @requests_mock.mock()
    def test_survey_help_for_bricks_with_sub_option_answer_a_survey_question(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        form = {"option": "answer-survey-question"}
        response = self.app.post(
            f"/surveys/help/help-completing-this-survey{self._help_details()}", data=form, follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Describe your issue and we will get back to you.".encode(), response.data)
        self.assertIn("Help answering a survey question".encode(), response.data)
        self.assertIn("Enter message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    def test_survey_help_for_bricks_with_sub_option_specific_figures_for_a_response(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        form = {"option": "do-not-have-specific-figures"}
        response = self.app.post(
            f"/surveys/help/help-completing-this-survey{self._help_details()}", data=form, follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("I do not have specific figures for a response".encode(), response.data)
        self.assertIn(
            "We do not expect you to spend too long or go to any great expense to get hold of the information we "
            "request.".encode(),
            response.data,
        )
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    def test_get_send_help_message_page_for_bricks_with_sub_option_specific_figures_for_a_response(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get(
            f"/surveys/help/help-completing-this-survey/do-not-have-specific-figures/send-message{self._help_details()}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Describe your issue and we will get back to you.".encode(), response.data)
        self.assertIn("I don’t have specific figures for a response".encode(), response.data)
        self.assertIn("Enter message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.views.surveys.help.surveys_help.get_survey")
    def test_survey_help_for_voluntary_survey_with_sub_option_unable_to_return_by_deadline(
        self, mock_request, get_survey
    ):
        mock_request.get(url_banner_api, status_code=404)
        form = {"option": "unable-to-return-by-deadline"}
        get_survey.return_value = {"legalBasisRef": "Vol_BEIS"}
        response = self.app.post(
            f"/surveys/help/help-completing-this-survey{self._help_details()}", data=form, follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("What if I cannot return the survey by the deadline?".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertNotIn(
            "If you do not contact us to discuss alternative arrangements or do not complete and return "
            "the survey, penalties may be incurred resulting in a fine of up to £2,500 (under section 4 "
            "of the Statistics of Trade Act 1947, last updated by section 17 of the Criminal Justice Act "
            "1991).".encode(),
            response.data,
        )
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.views.surveys.help.surveys_help.get_survey")
    def test_survey_help_for_statutory_survey_with_sub_option_unable_to_return_by_deadline(
        self, mock_request, get_survey
    ):
        mock_request.get(url_banner_api, status_code=404)
        form = {"option": "unable-to-return-by-deadline"}
        get_survey.return_value = {"legalBasisRef": "STA1947"}
        response = self.app.post(
            f"/surveys/help/help-completing-this-survey{self._help_details()}", data=form, follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("What if I cannot return the survey by the deadline?".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn(
            "If you do not contact us to discuss alternative arrangements or do not complete and return "
            "the survey, penalties may be incurred resulting in a fine of up to £2,500 (under section 4 "
            "of the Statistics of Trade Act 1947, last updated by section 17 of the Criminal Justice Act "
            "1991).".encode(),
            response.data,
        )
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    def test_get_send_help_message_page_for_bricks_with_deadline_sub_option_specific_figures_for_a_response(
        self, mock_request
    ):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get(
            f"/surveys/help/help-completing-this-survey/unable-to-return-by-deadline/send-message{self._help_details()}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Describe your issue and we will get back to you.".encode(), response.data)
        self.assertIn("I am unable to return the data by the deadline".encode(), response.data)
        self.assertIn("Enter message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    def test_survey_help_for_bricks_with_sub_option_something_else(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        form = {"option": "completing-this-survey-something-else"}
        response = self.app.post(
            f"/surveys/help/help-completing-this-survey{self._help_details()}", data=form, follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Describe your issue and we will get back to you.".encode(), response.data)
        self.assertIn("Help completing this survey".encode(), response.data)
        self.assertIn("Enter message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    @patch("frontstage.controllers.party_controller.get_survey_list_details_for_party")
    @patch("frontstage.views.surveys.help.surveys_help.send_message")
    def test_create_message_post_success(self, mock_request, send_message, get_survey_list, get_respondent_party_by_id):
        mock_request.get(url_banner_api, status_code=404)
        send_message.return_value = "a5e67f8a-0d90-4d60-a15a-7e334c75402b"
        get_survey_list.return_value = survey_list_todo
        form = {"body": "completing-this-survey-something-else"}
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post(
            f"/surveys/help/help-completing-this-survey/completing-this-survey-something-else/send-message{self._help_details()}",
            data=form,
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Message sent.".encode(), response.data)

    @requests_mock.mock()
    def test_account_help_redirects_correctly(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, json=respondent_party, status_code=200)
        form = {"option": "help-with-my-account"}
        response = self.app.post(f"/surveys/help{self._help_details()}", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Account details".encode(), response.data)
        self.assertIn("Change my contact details".encode(), response.data)

    @staticmethod
    def _help_details():
        return (
            "?survey_name=Monthly+Survey+of+Building+Materials+Bricks"
            "&survey_id=cb8accda-6118-4d3b-85a3-149e28960c54"
            "&business_id=5e03702d-1d02-4b13-9e0e-ab9e79863d08"
            "&ce_id=3bc7ccf0-638b-4a05-a3dc-9847c4354d90"
        )
