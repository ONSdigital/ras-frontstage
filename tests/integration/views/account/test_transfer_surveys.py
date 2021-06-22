import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from tests.integration.mocked_services import encoded_jwt_token, respondent_party, url_banner_api, \
    url_get_respondent_party, url_get_survey, business_party, survey

url_get_business_details = f"{app.config['PARTY_URL']}/party-api/v1/businesses"
url_get_user_count = f"{app.config['PARTY_URL']}/party-api/v1/pending-survey-users-count?business_id={business_party['id']}&survey_id={'02b9c366-7397-42f7-942a-76dc5876d86d'}"
url_post_pending_transfers = f"{app.config['PARTY_URL']}/party-api/v1/pending-surveys"
url_get_survey_second = f"{app.config['SURVEY_URL']}/surveys/02b9c366-7397-42f7-942a-76dc5876d86d"
dummy_business = {'associations': [{'businessRespondentStatus': 'ACTIVE',
                                    'enrolments': [{'enrolmentStatus': 'ENABLED',
                                                    'surveyId': '02b9c366-7397-42f7-942a-76dc5876d86d'}],
                                    'partyId': '9f26eb0e-7db7-41fd-9c4c-3ee9f562aa35'}],
                  'id': 'd7813ec7-10c3-4872-8717-c0b9135f917c',
                  'name': 'RUNAME1_COMPANY1 RUNNAME2_COMPANY1',
                  'sampleSummaryId': 'e502324d-6e49-4fcb-8c68-e6553f45fae1',
                  'sampleUnitRef': '49900000001', 'sampleUnitType': 'B',
                  'trading_as': 'TOTAL UK ACTIVITY'}
dummy_survey = {"id": "02b9c366-7397-42f7-942a-76dc5876d86d",
                "shortName": "QBS", "longName": "Quarterly Business Survey", "surveyRef": "139",
                "legalBasis": "Statistics of Trade Act 1947", "surveyType": "Business", "surveyMode": "EQ",
                "legalBasisRef": "STA1947"}


class TestTransferSurvey(unittest.TestCase):

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
    def test_transfer_survey_business_select(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=[dummy_business])
        response = self.app.get('/my-account/transfer-surveys/business-selection')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('For which businesses do you want to transfer your surveys?'.encode() in response.data)
        self.assertTrue('Select all that apply'.encode() in response.data)
        self.assertTrue('RUNAME1_COMPANY1 RUNNAME2_COMPANY1'.encode() in response.data)
        self.assertTrue('Continue'.encode() in response.data)
        self.assertTrue('Cancel'.encode() in response.data)

    @requests_mock.mock()
    def test_transfer_survey_business_select_no_option_selected(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=[dummy_business])
        response = self.app.post('/my-account/transfer-surveys/business-selection',
                                 data={"option": None},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("You need to choose a business".encode(), response.data)

    @requests_mock.mock()
    def test_transfer_survey_select(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=[business_party])
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        response = self.app.post('/my-account/transfer-surveys/business-selection',
                                 data={"checkbox-answer": '99941a3f-8e32-40e4-b78a-e039a2b437ca'},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Which surveys do you want to transfer?".encode(), response.data)
        self.assertIn("Monthly Survey of Building Materials Bricks".encode(), response.data)
        self.assertIn("Select all that apply".encode(), response.data)
        self.assertIn("Monthly Survey of Building Materials Bricks".encode(), response.data)
        self.assertIn("Quarterly Business Survey".encode(), response.data)
        self.assertTrue('Continue'.encode() in response.data)
        self.assertTrue('Cancel'.encode() in response.data)

    @requests_mock.mock()
    def test_transfer_survey_select_no_option_selected(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=[business_party])
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        with self.app.session_transaction() as mock_session:
            mock_session['transfer_survey_data'] = {business_party['id']: None}
        response = self.app.post('/my-account/transfer-surveys/survey-selection',
                                 data={"option": None},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("Select an answer".encode(), response.data)
        self.assertIn("You need to select a survey".encode(), response.data)

    @requests_mock.mock()
    def test_transfer_survey_select_option_selected(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=[business_party])
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        mock_request.get(url_get_user_count, status_code=200, json=2)
        with self.app.session_transaction() as mock_session:
            mock_session['transfer_survey_data'] = {business_party['id']: None}
        response = self.app.post('/my-account/transfer-surveys/survey-selection',
                                 data={business_party['name']: ['02b9c366-7397-42f7-942a-76dc5876d86d']},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Enter recipient's email address".encode(), response.data)
        self.assertIn("We need the email address of the person who will be responding to the surveys.".encode(),
                      response.data)
        self.assertIn("Recipient's email address".encode(), response.data)
        self.assertIn("Make sure you have their permission to give us their email address.".encode(), response.data)
        self.assertTrue('Continue'.encode() in response.data)
        self.assertTrue('Cancel'.encode() in response.data)

    @requests_mock.mock()
    def test_transfer_survey_select_option_selected_fails_max_user_validation(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=[business_party])
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        mock_request.get(url_get_user_count, status_code=200, json=52)
        with self.app.session_transaction() as mock_session:
            mock_session['transfer_survey_data'] = {business_party['id']: None}
        response = self.app.post('/my-account/transfer-surveys/survey-selection',
                                 data={business_party['name']: ['02b9c366-7397-42f7-942a-76dc5876d86d']},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("You have reached the maximum amount of emails you can enroll on one or more surveys".encode(),
                      response.data)
        self.assertIn("Deselect the survey/s to continue or call 0300 1234 931 to discuss your options.".encode(),
                      response.data)

    @requests_mock.mock()
    def test_transfer_survey_recipient_email_not_entered(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=[business_party])
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        with self.app.session_transaction() as mock_session:
            mock_session['transfer_survey_data'] = {business_party['id']: [survey['id']]}
        response = self.app.post('/my-account/transfer-surveys/recipient-email-address',
                                 data={},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("There is 1 error on this page".encode(), response.data)
        self.assertIn("Problem with the email address".encode(), response.data)
        self.assertIn("You need to enter an email address".encode(), response.data)

    @requests_mock.mock()
    def test_transfer_survey_recipient_email_invalid(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=business_party)
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=[dummy_survey])
        with self.app.session_transaction() as mock_session:
            mock_session['transfer_survey_data'] = {business_party['id']: [survey['id']]}
        response = self.app.post('/my-account/transfer-surveys/recipient-email-address',
                                 data={'email_address': 'a.a.com'},
                                 follow_redirects=True)
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
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        with self.app.session_transaction() as mock_session:
            mock_session['transfer_survey_data'] = {business_party['id']: [survey['id']]}
        response = self.app.post('/my-account/transfer-surveys/recipient-email-address',
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
    def test_transfer_survey_transfer_instruction_done(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=[business_party])
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        mock_request.post(url_post_pending_transfers, status_code=201, json={'created': 'success'})

        with self.app.session_transaction() as mock_session:
            mock_session['transfer_survey_data'] = {business_party['id']: [survey['id']]}
            mock_session['transfer_survey_recipient_email_address'] = 'a@a.com'
        response = self.app.post('/my-account/transfer-surveys/send-instruction',
                                 data={'email_address': 'a@a.com'},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("We have sent an email to the new person who will be responding to ONS surveys.".encode(),
                      response.data)
        self.assertTrue('They need to follow the link in the email to confirm their email address and finish setting '
                        'up their account.'.encode() in response.data)
        self.assertIn("Email not arrived? It may be in their junk folder.".encode(), response.data)
        self.assertIn("If it does not arrive in the next 15 minutes, please call 0300 1234 931.".encode(),
                      response.data)
        self.assertTrue('Back to surveys'.encode() in response.data)
