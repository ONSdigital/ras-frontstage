import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from tests.integration.mocked_services import (
    business_party,
    encoded_jwt_token,
    respondent_party,
    survey,
    survey_eq,
    survey_list_todo,
    survey_rsi,
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
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_qbs(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey_eq
        get_business.return_value = business_party
        response = self.app.get("/surveys/surveys-help?survey_ref=139&ru_ref=49900000001F", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Help".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("Information about the Quarterly Business Survey".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_bricks(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        response = self.app.get("/surveys/surveys-help?survey_ref=074&ru_ref=49900000001F", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Help".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("Information about the Monthly Survey of Building Materials Bricks".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)
        self.assertIn("Help".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_bricks_with_no_option_select(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {}
        self.set_flask_session()
        response = self.app.post("/surveys/help", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Error: ".encode(), response.data)
        self.assertIn('<span class="ons-panel__assistive-text ons-u-vh">Error: </span>'.encode(), response.data)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("You need to choose an option".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_bricks_with_option_select(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {"option": "info-about-this-survey"}
        self.set_flask_session()
        response = self.app.post("/surveys/help", data=form, follow_redirects=True)

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
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_bricks_with_sub_option_exemption_completing_survey(
        self, mock_request, get_survey, get_business
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {"option": "exemption-completing-survey"}
        self.set_flask_session()
        response = self.app.post("/surveys/help/info-about-this-survey", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Can I be exempt from completing the survey questionnaire?".encode(), response.data)
        self.assertIn(
            "While this survey is voluntary, we have selected your company in the same way we ".encode(), response.data
        )
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_rsi_with_sub_option_exemption_completing_survey(
        self, mock_request, get_survey, get_business
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey_rsi
        get_business.return_value = business_party
        form = {"option": "exemption-completing-survey"}
        self.set_flask_session()
        response = self.app.post("/surveys/help/info-about-this-survey", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Can I be exempt from completing the survey questionnaire?".encode(), response.data)
        self.assertIn(
            "No. Once selected, the law obliges a business to complete the survey under the provisions "
            "of the Statistics of Trade Act 1947".encode(),
            response.data,
        )
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_bricks_with_sub_option_why_selected(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {"option": "why-selected"}
        self.set_flask_session()
        response = self.app.post("/surveys/help/info-about-this-survey", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("How was my business selected?".encode(), response.data)
        self.assertIn(
            "We select businesses from the Inter-Departmental Business Register (IDBR). ".encode(), response.data
        )
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_bricks_with_sub_option_time_to_complete(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {"option": "time-to-complete"}
        self.set_flask_session()
        response = self.app.post("/surveys/help/info-about-this-survey", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("How long will it take to complete?".encode(), response.data)
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_bricks_with_sub_option_how_long_selected_for(
        self, mock_request, get_survey, get_business
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {"option": "how-long-selected-for"}
        self.set_flask_session()
        response = self.app.post("/surveys/help/info-about-this-survey", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("How long will my business be selected for?".encode(), response.data)
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_for_voluntary_survey_with_sub_option_penalties(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {"option": "penalties"}
        self.set_flask_session()
        response = self.app.post("/surveys/help/info-about-this-survey", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Are there penalties for not completing this survey?".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertNotIn(
            "If you do not contact us or complete and return by the deadline, penalties may be incurred "
            "resulting in a fine of up to £2,500 (under section 4 of the Statistics of Trade Act 1947, "
            "last updated by section 17 of the Criminal Justice Act 1991).".encode(),
            response.data,
        )
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_for_statutory_survey_with_sub_option_penalties(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey_eq
        get_business.return_value = business_party
        form = {"option": "penalties"}
        self.set_flask_session()
        response = self.app.post("/surveys/help/info-about-this-survey", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Are there penalties for not completing this survey?".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn(
            "If you do not contact us or complete and return by the deadline, penalties may be incurred "
            "resulting in a fine of up to £2,500 (under section 4 of the Statistics of Trade Act 1947, "
            "last updated by section 17 of the Criminal Justice Act 1991).".encode(),
            response.data,
        )
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_info_bricks_with_sub_option_something_else(self, mock_request, get_survey, get_business):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        form = {"option": "info-something-else"}
        self.set_flask_session()
        response = self.app.post("/surveys/help/info-about-this-survey", data=form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Information about the Monthly Survey of Building Materials Bricks".encode(), response.data)
        self.assertIn("https://www.ons.gov.uk/surveys/informationforbusinesses".encode(), response.data)
        self.assertIn("Did this answer your question?".encode(), response.data)
        self.assertIn("Yes".encode(), response.data)
        self.assertIn("No".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_send_message_info_bricks_with_sub_option_exemption_completing_survey(
        self, mock_request, get_survey, get_business
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        self.set_flask_session()
        response = self.app.get(
            "/surveys/help/info-about-this-survey/" "exemption-completing-survey/send-message",
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Can I be exempt from completing the survey questionnaire?".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_send_message_info_bricks_with_sub_option_why_selected_survey(
        self, mock_request, get_survey, get_business
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        self.set_flask_session()
        response = self.app.get(
            "/surveys/help/info-about-this-survey/" "why-selected/send-message", follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("How  was my business selected?".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_send_message_info_bricks_with_sub_option_time_to_complete(
        self, mock_request, get_survey, get_business
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        self.set_flask_session()
        response = self.app.get(
            "/surveys/help/info-about-this-survey/" "time-to-complete/send-message",
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("How long will it take to complete?".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_send_message_info_bricks_with_sub_option_how_long_selected_for(
        self, mock_request, get_survey, get_business
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        self.set_flask_session()
        response = self.app.get(
            "/surveys/help/info-about-this-survey/how-long-selected-for/send-message",
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Describe your issue and we will get back to you.".encode(), response.data)
        self.assertIn("How long will my business be selected for?".encode(), response.data)
        self.assertIn("Enter message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_send_message_info_bricks_with_sub_option_penalties(
        self, mock_request, get_survey, get_business
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        self.set_flask_session()
        response = self.app.get("/surveys/help/info-about-this-survey/penalties/send-message", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Describe your issue and we will get back to you.".encode(), response.data)
        self.assertIn("What are the penalties for not completing a survey?".encode(), response.data)
        self.assertIn("Enter message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_survey_help_send_message_info_bricks_with_sub_option_info_something_else(
        self, mock_request, get_survey, get_business
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        self.set_flask_session()
        response = self.app.get(
            "/surveys/help/info-about-this-survey/info-something-else/send-message",
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Send a message".encode(), response.data)
        self.assertIn("Describe your issue and we will get back to you.".encode(), response.data)
        self.assertIn("Information about this survey".encode(), response.data)
        self.assertIn("Enter message".encode(), response.data)
        self.assertIn("Send message".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    @patch("frontstage.controllers.party_controller.get_survey_list_details_for_party")
    @patch("frontstage.controllers.conversation_controller.send_message")
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_create_message_post_success(
        self, mock_request, get_survey, get_business, send_message, get_survey_list, get_respondent_party_by_id
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        get_survey_list.return_value = survey_list_todo
        get_respondent_party_by_id.return_value = respondent_party
        form = {"body": "info-something-else"}
        self.set_flask_session()
        response = self.app.post(
            "/surveys/help/info-about-this-survey/info-something-else/send-message",
            data=form,
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Message sent.".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    @patch("frontstage.controllers.party_controller.get_survey_list_details_for_party")
    @patch("frontstage.controllers.conversation_controller.send_message")
    @patch("frontstage.controllers.party_controller.get_business_by_ru_ref")
    @patch("frontstage.controllers.survey_controller.get_survey_by_survey_ref")
    def test_create_message_post_failure(
        self, mock_request, get_survey, get_business, send_message, get_survey_list, get_respondent_party_by_id
    ):
        mock_request.get(url_banner_api, status_code=404)
        get_survey.return_value = survey
        get_business.return_value = business_party
        get_survey_list.return_value = survey_list_todo
        get_respondent_party_by_id.return_value = respondent_party
        form = {"body": ""}
        self.set_flask_session()
        response = self.app.post(
            "/surveys/help/info-about-this-survey/info-something-else/send-message",
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
        self.assertIn("Information about this survey".encode(), response.data)
