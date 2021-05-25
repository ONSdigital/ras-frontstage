import unittest
import uuid
from unittest.mock import patch

import requests_mock

from frontstage import app
from tests.integration.mocked_services import encoded_jwt_token, respondent_party, url_banner_api, \
    url_get_respondent_party, url_get_survey, business_party, survey

token = 'ImM0NWM3ZDZmLWNlZjItNDMxOS1hNjA3LTU1MDczODA2ODkwNSI.YKZonA.HL-QGEm9Bvdwr7F-r3Z7sI267Cc'
batch_number = '02b9c366-7397-42f7-942a-76dc5876d86d'
url_get_share_survey_verify = f"{app.config['PARTY_URL']}/party-api/v1/share-survey/verification/{token}"
url_post_accept_share_survey = f"{app.config['PARTY_URL']}/party-api/v1/share-survey/confirm-pending-shares/" \
                               f"{batch_number}"
url_get_shared_by_respondent_party = f"{app.config['PARTY_URL']}/party-api/v1/respondents/id/sharetest@test.com"
url_get_business_details = f"{app.config['PARTY_URL']}/party-api/v1/businesses"
url_get_user_count = f"{app.config['PARTY_URL']}/party-api/v1/share-survey-users-count?business_id={business_party['id']}&survey_id={'02b9c366-7397-42f7-942a-76dc5876d86d'}"
url_post_pending_shares = f"{app.config['PARTY_URL']}/party-api/v1/pending-shares"
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

dummy_pending_share = {
    'email_address': 'test@test.com',
    'business_id': 'd7813ec7-10c3-4872-8717-c0b9135f917c',
    'survey_id': '02b9c366-7397-42f7-942a-76dc5876d86d',
    'shared_by': 'sharetest@test.com',
    'batch_no': str(uuid.uuid1())
}


class TestAcceptShareSurvey(unittest.TestCase):

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
    def test_get_share_survey_summary_success(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_shared_by_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=[dummy_business])
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        mock_request.get(url_get_share_survey_verify, status_code=200, json=[dummy_pending_share])
        response = self.app.get(f'/my-account/share-surveys/accept-share-surveys/{token}')
        self.assertEqual(response.status_code, 200)
        self.assertIn("Confirm survey access".encode(), response.data)
        self.assertIn("RUNAME1_COMPANY1 RUNNAME2_COMPANY1".encode(), response.data)
        self.assertIn("Trading as TOTAL UK ACTIVITY".encode(), response.data)
        self.assertIn("Quarterly Business Survey".encode(), response.data)
        self.assertIn("Accept".encode(), response.data)

    @requests_mock.mock()
    def test_get_share_survey_summary_expired_token(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=[dummy_business])
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        mock_request.get(url_get_share_survey_verify, status_code=409)
        response = self.app.get(f'/my-account/share-surveys/accept-share-surveys/{token}')
        self.assertEqual(409, response.status_code)

    @requests_mock.mock()
    def test_get_share_survey_summary_not_found(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=[dummy_business])
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        mock_request.get(url_get_share_survey_verify, status_code=404)
        response = self.app.get(f'/my-account/share-surveys/accept-share-surveys/{token}')
        self.assertEqual(404, response.status_code)

    @requests_mock.mock()
    @patch('frontstage.controllers.party_controller.get_survey_list_details_for_party')
    def test_get_accept_share_surveys_success(self, mock_request, get_survey_list):
        survey_list = [{"case_id": "6f698975-0a36-45ff-ba66-7a575e414023",
                        "status": "Not started", "collection_instrument_type": "EQ",
                        "survey_id": "02b9c366-7397-42f7-942a-76dc5876d86d",
                        "survey_long_name": "Quarterly Business Survey",
                        "survey_short_name": "QBS", "survey_ref": "139",
                        "business_party_id": "44d8db36-2319-41c6-8887-79033ce55a4b",
                        "business_name": "PC UNIVERSE", "trading_as": "PC LTD",
                        "business_ref": "49900000007", "period": "December 2019",
                        "submit_by": "26 Mar 2021", "collection_exercise_ref": "1912",
                        "added_survey": None, "display_button": True}]
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=[dummy_business])
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        mock_request.post(url_post_accept_share_survey, status_code=201)
        get_survey_list.return_value = survey_list
        response = self.app.get(f'/my-account/confirm-share-surveys/{batch_number}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    @requests_mock.mock()
    def test_get_accept_share_surveys_fail(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_get_business_details, status_code=200, json=[dummy_business])
        mock_request.get(url_get_survey, status_code=200, json=survey)
        mock_request.get(url_get_survey_second, status_code=200, json=dummy_survey)
        mock_request.post(url_post_accept_share_survey, status_code=404)
        response = self.app.get(f'/my-account/confirm-share-surveys/{batch_number}', follow_redirects=True)
        self.assertEqual(response.status_code, 500)
