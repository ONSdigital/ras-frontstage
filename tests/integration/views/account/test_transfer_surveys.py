import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from frontstage.exceptions.exceptions import TransferSurveyProcessError
from tests.integration.mocked_services import (
    business_party,
    encoded_jwt_token,
    party,
    respondent_enrolments,
    respondent_party,
    survey,
    url_banner_api,
    url_get_respondent_party,
    url_get_survey,
)

url_get_business_details = f"{app.config['PARTY_URL']}/party-api/v1/businesses"
url_get_user_count = (
    f"{app.config['PARTY_URL']}/party-api/v1/pending-survey-users-count?"
    f"business_id={business_party['id']}&survey_id={'02b9c366-7397-42f7-942a-76dc5876d86d'}"
)
url_post_pending_transfers = f"{app.config['PARTY_URL']}/party-api/v1/pending-surveys"

selected_surveys = {
    "selected_surveys": [
        "{'business_id': 'be3483c3-f5c9-4b13-bdd7-244db78ff687', 'survey_id': "
        "'02b9c366-7397-42f7-942a-76dc5876d86d'}"
    ]
}


class TestTransferSurvey(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie("authorization", "session_key")
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2Vy"
            "X3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"
            # NOQA
        }
        self.patcher = patch("redis.StrictRedis.get", return_value=encoded_jwt_token)
        self.empty_form = {}
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @requests_mock.mock()
    @patch("frontstage.views.account.account_transfer_survey.get_respondent_enrolments")
    def test_transfer_survey_select(self, mock_request, get_respondent_enrolments):
        mock_request.get(url_banner_api, status_code=404)
        get_respondent_enrolments.return_value = respondent_enrolments

        response = self.app.get("/my-account/transfer-surveys/survey-selection")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Transfer your surveys".encode(), response.data)
        self.assertIn("Choose the surveys you want to transfer".encode(), response.data)
        self.assertIn("Survey 1".encode(), response.data)
        self.assertIn("Select all that apply".encode(), response.data)
        self.assertIn("Survey 2".encode(), response.data)
        self.assertTrue("Continue".encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.views.account.account_transfer_survey.get_respondent_enrolments")
    def test_transfer_survey_select_no_option_selected(self, mock_request, get_respondent_enrolments):
        mock_request.get(url_banner_api, status_code=404)
        get_respondent_enrolments.return_value = respondent_enrolments

        response = self.app.post(
            "/my-account/transfer-surveys/survey-selection", data={"option": None}, follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("You need to select a survey".encode(), response.data)

    @requests_mock.mock()
    def test_transfer_survey_select_option_selected(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_user_count, status_code=200, json=2)

        response = self.app.post(
            "/my-account/transfer-surveys/survey-selection",
            data=selected_surveys,
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("New respondents email address".encode(), response.data)
        self.assertIn("We will send instructions to the email address that you provide.".encode(), response.data)
        self.assertIn(
            "Once we confirm the new respondents access, they will be able to respond to the surveys you have selected.".encode(),
            response.data,
        )
        self.assertIn("New respondents email address".encode(), response.data)
        self.assertIn("Make sure you have permission to give us their email address.".encode(), response.data)
        self.assertTrue("Continue".encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.views.account.account_transfer_survey.get_respondent_enrolments")
    def test_transfer_survey_select_option_selected_fails_max_user_validation(
        self, mock_request, get_respondent_enrolments
    ):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_user_count, status_code=200, json=52)
        get_respondent_enrolments.return_value = respondent_enrolments

        response = self.app.post(
            "/my-account/transfer-surveys/survey-selection",
            data=selected_surveys,
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn(
            "You have reached the maximum amount of emails you can enroll on one or more surveys".encode(),
            response.data,
        )
        self.assertIn(
            "Deselect the survey/s to continue or call 0300 1234 931 to discuss your options.".encode(), response.data
        )

    @requests_mock.mock()
    def test_transfer_survey_recipient_email_not_entered(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)

        response = self.app.post("/my-account/transfer-surveys/recipient-email-address", data={}, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("Problem with the email address".encode(), response.data)
        self.assertIn("You need to enter an email address".encode(), response.data)

    @requests_mock.mock()
    def test_transfer_survey_recipient_email_invalid(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)

        response = self.app.post(
            "/my-account/transfer-surveys/recipient-email-address",
            data={"email_address": "a.a.com"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("Problem with the email address".encode(), response.data)
        self.assertIn("Invalid email address".encode(), response.data)

    @requests_mock.mock()
    def test_transfer_survey_transfer_instruction(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=[business_party])
        mock_request.get(url_get_survey, status_code=200, json=survey)
        with self.app.session_transaction() as mock_session:
            mock_session["surveys_to_transfer_map"] = {business_party["id"]: [survey["id"]]}
        response = self.app.post(
            "/my-account/transfer-surveys/recipient-email-address",
            data={"email_address": "a@a.com"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Send instructions".encode(), response.data)
        self.assertIn(
            "We will email a link with instructions to <strong>a@a.com</strong>.".encode(),
            response.data,
        )
        self.assertIn("Once approved, they will have access to:".encode(), response.data)
        self.assertIn("RUNAME1_COMPANY1 RUNNAME2_COMPANY1".encode(), response.data)
        self.assertIn("Monthly Survey of Building Materials Bricks".encode(), response.data)
        self.assertTrue("Send".encode() in response.data)

    @requests_mock.mock()
    def test_transfer_survey_transfer_instruction_done(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=[business_party])
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.post(url_post_pending_transfers, status_code=201, json={"created": "success"})

        with self.app.session_transaction() as mock_session:
            mock_session["surveys_to_transfer_map"] = {business_party["id"]: [survey["id"]]}
            mock_session["transfer_survey_recipient_email_address"] = "a@a.com"
        response = self.app.post(
            "/my-account/transfer-surveys/send-instruction", data={"email_address": "a@a.com"}, follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Instructions sent".encode(), response.data)
        self.assertIn("An email with instructions has been sent to <strong>a@a.com</strong>.".encode(), response.data)
        self.assertTrue(
            "They will need to follow the link in this email to confirm their email address and finish setting up "
            "their account.".encode() in response.data
        )
        self.assertIn("This email might go to a junk or spam folder.".encode(), response.data)
        self.assertIn(
            "If they do not receive this email in 15 minutes, call us on +44 300 1234 931".encode(), response.data
        )
        self.assertTrue("Back to surveys".encode() in response.data)

    @requests_mock.mock()
    def test_transfer_survey_transfer_instruction_transfer_already_exists(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=[business_party])
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.post(url_post_pending_transfers, status_code=400, json={"error": "error"})
        with self.app.session_transaction() as mock_session:
            mock_session["surveys_to_transfer_map"] = {business_party["id"]: [survey["id"]]}
            mock_session["transfer_survey_recipient_email_address"] = "a@a.com"

        response = self.app.post(
            "/my-account/transfer-surveys/send-instruction", data={"email_address": "a@a.com"}, follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "You have already shared or transferred these surveys with someone with this email address. "
            "They have 72 hours to accept your request. If you have made an error then wait for the "
            "share/transfer to expire or contact us.".encode(),
            response.data,
        )
        self.assertIn(
            "We will email a link with instructions to <strong>a@a.com</strong>.".encode(),
            response.data,
        )
        self.assertIn("Once approved, they will have access to:".encode(), response.data)
        self.assertIn("RUNAME1_COMPANY1 RUNNAME2_COMPANY1".encode(), response.data)
        self.assertIn("Monthly Survey of Building Materials Bricks".encode(), response.data)
        self.assertTrue("Send".encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.views.account.account_transfer_survey.get_respondent_enrolments")
    def test_transfer_survey(self, mock_request, get_respondent_enrolments):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_survey, status_code=200, json=survey)
        get_respondent_enrolments.return_value = respondent_enrolments

        response = self.app.get(
            "/my-account/transfer-surveys/", data={"email_address": "a@a.com"}, follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Transfer your surveys".encode(), response.data)
        self.assertIn(
            "If you transfer a survey, you will no longer have access to it. If you will still need access "
            "to the survey,".encode(),
            response.data,
        )
        self.assertIn("Business 1".encode(), response.data)
        self.assertIn("Choose the surveys you want to transfer".encode(), response.data)
        self.assertIn("Survey 1".encode(), response.data)
        self.assertTrue("Continue".encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    def test_transfer_survey_recipient_email_same_as_user(self, mock_request, get_respondent_party_by_id):
        mock_request.get(url_banner_api, status_code=404)
        get_respondent_party_by_id.return_value = party

        response = self.app.post(
            "/my-account/transfer-surveys/recipient-email-address",
            data={"email_address": "example@example.com"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("Problem with the email address".encode(), response.data)
        self.assertIn("You can not transfer surveys to yourself.".encode(), response.data)

    @requests_mock.mock()
    def test_transfer_survey_transfer_survey_process_error(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)

        with self.app.session_transaction() as mock_session:
            mock_session["transfer_survey_recipient_email_address"] = "a@a.com"

        response = self.app.post("/my-account/transfer-surveys/send-instruction", data={}, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertRaises(TransferSurveyProcessError)
        self.assertLogs("Could not find email address in session", response.data)
