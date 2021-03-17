import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from frontstage.common.session import Session
from frontstage.exceptions.exceptions import ShareSurveyProcessError
from tests.integration.mocked_services import encoded_jwt_token, respondent_party, url_banner_api, \
    url_get_respondent_party, url_get_survey, business_party, survey

url_get_business_details = f"{app.config['PARTY_URL']}/party-api/v1/businesses"
url_get_survey_second = f"{app.config['SURVEY_URL']}/surveys/02b9c366-7397-42f7-942a-76dc5876d86d"
dummy_business = [{'associations': [{'businessRespondentStatus': 'ACTIVE',
                                     'enrolments': [{'enrolmentStatus': 'ENABLED',
                                                     'surveyId': '02b9c366-7397-42f7-942a-76dc5876d86d'}],
                                     'partyId': '9f26eb0e-7db7-41fd-9c4c-3ee9f562aa35'}],
                   'id': 'd7813ec7-10c3-4872-8717-c0b9135f917c',
                   'name': 'RUNAME1_COMPANY1 RUNNAME2_COMPANY1',
                   'sampleSummaryId': 'e502324d-6e49-4fcb-8c68-e6553f45fae1',
                   'sampleUnitRef': '49900000001', 'sampleUnitType': 'B',
                   'trading_as': 'TOTAL UK ACTIVITY'}]
dummy_survey = {"id": "02b9c366-7397-42f7-942a-76dc5876d86d",
                "shortName": "QBS", "longName": "Quarterly Business Survey", "surveyRef": "139",
                "legalBasis": "Statistics of Trade Act 1947", "surveyType": "Business", "surveyMode": "EQ",
                "legalBasisRef": "STA1947"}


class TestSurveyList(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie('localhost', 'authorization', 'session_key')
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"
            # NOQA
        }
        self.patcher = patch('redis.StrictRedis.get', return_value=encoded_jwt_token)
        self.empty_form = {
        }
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @requests_mock.mock()
    def test_share_survey_business_select(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=dummy_business)
        response = self.app.get('/my-account/share-surveys/business-selection')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Which of your business’s surveys do you want to share?'.encode() in response.data)
        self.assertTrue('Choose a business'.encode() in response.data)
        self.assertTrue('RUNAME1_COMPANY1 RUNNAME2_COMPANY1'.encode() in response.data)
        self.assertTrue('Continue'.encode() in response.data)
        self.assertTrue('Cancel'.encode() in response.data)

    @requests_mock.mock()
    def test_share_survey_business_select_no_option_selected(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=dummy_business)
        response = self.app.post('/my-account/share-surveys/business-selection',
                                 data={"option": None},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("You need to select a business".encode(), response.data)

    @requests_mock.mock()
    def test_share_survey_select(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=business_party)
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        response = self.app.post('/my-account/share-surveys/business-selection',
                                 data={"option": '99941a3f-8e32-40e4-b78a-e039a2b437ca'},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Which surveys do you want to share?".encode(), response.data)
        self.assertIn("ACME Consumer Products".encode(), response.data)
        self.assertIn("Select all that apply".encode(), response.data)
        self.assertIn("Monthly Survey of Building Materials Bricks".encode(), response.data)
        self.assertIn("Quarterly Business Survey".encode(), response.data)
        self.assertTrue('Continue'.encode() in response.data)
        self.assertTrue('Cancel'.encode() in response.data)

    @requests_mock.mock()
    def test_share_survey_select_no_option_selected(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=business_party)
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        with self.app.session_transaction() as mock_session:
            mock_session['business_selected'] = business_party['id']
        response = self.app.post('/my-account/share-surveys/survey-selection',
                                 data={"option": None},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("You need to select a survey".encode(), response.data)
        self.assertIn("You need to choose at least one option".encode(), response.data)

    @requests_mock.mock()
    def test_share_survey_select_option_selected(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=business_party)
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        with self.app.session_transaction() as mock_session:
            mock_session['business_selected'] = business_party['id']
        response = self.app.post('/my-account/share-surveys/survey-selection',
                                 data={"checkbox-answer": ['02b9c366-7397-42f7-942a-76dc5876d86d']},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Enter recipient's email address".encode(), response.data)
        self.assertIn("Make sure you have permission from the recipient to provide their email address to us.".encode(),
                      response.data)
        self.assertIn("Recipient's email address".encode(), response.data)
        self.assertIn("This is the person who will be able to respond to your surveys.".encode(), response.data)
        self.assertTrue('Continue'.encode() in response.data)
        self.assertTrue('Cancel'.encode() in response.data)

    @requests_mock.mock()
    def test_share_survey_recipient_email_not_entered(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=business_party)
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        with self.app.session_transaction() as mock_session:
            mock_session['business_selected'] = business_party['id']
            mock_session['surveys_selected'] = survey['id']
        response = self.app.post('/my-account/share-surveys/recipient-email-address',
                                 data={},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("Problem with the email address".encode(), response.data)
        self.assertIn("You need to enter an email address".encode(), response.data)

    @requests_mock.mock()
    def test_share_survey_recipient_email_invalid(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=business_party)
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        with self.app.session_transaction() as mock_session:
            mock_session['business_selected'] = business_party['id']
            mock_session['surveys_selected'] = survey['id']
        response = self.app.post('/my-account/share-surveys/recipient-email-address',
                                 data={'email_address': 'a.a.com'},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("Problem with the email address".encode(), response.data)
        self.assertIn("Invalid email address".encode(), response.data)

    @requests_mock.mock()
    def test_share_survey_share_instruction(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=business_party)
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        with self.app.session_transaction() as mock_session:
            mock_session['business_selected'] = business_party['id']
            mock_session['surveys_selected'] = [survey['id']]
        response = self.app.post('/my-account/share-surveys/recipient-email-address',
                                 data={'email_address': 'a@a.com'},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Send instructions".encode(), response.data)
        self.assertIn("will send an email to <b>a@a.com</b> with instructions to access the following surveys:".
                      encode(),
                      response.data)
        self.assertIn("Monthly Survey of Building Materials Bricks".encode(), response.data)
        self.assertTrue('Send'.encode() in response.data)
        self.assertTrue('Cancel'.encode() in response.data)

    @requests_mock.mock()
    def test_share_survey_share_instruction_done(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=business_party)
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        with self.app.session_transaction() as mock_session:
            mock_session['business_selected'] = business_party['id']
            mock_session['surveys_selected'] = [survey['id']]
            mock_session['recipient_email_address'] = 'a@a.com'
        response = self.app.post('/my-account/share-surveys/send-instruction',
                                 data={'email_address': 'a@a.com'},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("We have sent an email to the new respondent.".encode(), response.data)
        self.assertTrue('Once they have received it, they need to follow the link in the email to confirm their email '
                        'address and finish setting up their account.'.encode() in response.data)
        self.assertIn("Email not arrived? It might be in their spam folder.".encode(), response.data)
        self.assertIn("If it doesn’t arrive in the next 15 minutes, please call 0300 1234 931.".encode(), response.data)
        self.assertTrue('Back to surveys'.encode() in response.data)
