import unittest
from app.application import app
from app.config import Config, TestingConfig
import json
import requests_mock

with open('tests/test_data/my_surveys.json') as json_data:
    my_surveys_data = json.load(json_data)

with open('tests/test_data/collection_instrument.json') as json_data:
    collection_instrument_data = json.load(json_data)

with open('tests/test_data/cases.json') as json_data:
    cases_data = json.load(json_data)


# print("Test data JSON values are:{}".format(collection_instrument_data))

returned_token = {
    "id": 6,
    "access_token": "a712f0f9-d00d-447a-b143-49984ca3db68",
    "expires_in": 3600,
    "token_type": "Bearer",
    "scope": "",
    "refresh_token": "37ca04d2-6b6c-4854-8e85-f59c2cc7d3de",
    "party_id": "3b136c4b-7a14-4904-9e01-13364dd7b972"

}

case_id = '7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb'
collection_instrument_id = '40c7c047-4fb3-4abe-926e-bf19fa2c0a1e'
#party_id = '3b136c4b-7a14-4904-9e01-13364dd7b972'
party_id = "db036fd7-ce17-40c2-a8fc-932e7c228397"


class TestSurveys(unittest.TestCase):
    """Test case for application endpoints and functionality"""

    def setUp(self):

        self.app = app.test_client()
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
            }

    # Test we get survey data once a user signs in properly. This means we have to mock up OAuth2 server sending a
    # Token. The ras_frontstage will then send a request for data to the API Gateway / Party Service, we Mock this too
    # and reply with survey data. See: https://requests-mock.readthedocs.io/en/latest/response.html
    @requests_mock.mock()
    def test_sign_in_view_survey_data(self, mock_object):
        """Test we display survey data after signing in correctly"""

        # Build mock URL's which are used to provide application data
        url_get_token = Config.ONS_OAUTH_PROTOCOL + Config.ONS_OAUTH_SERVER + Config.ONS_TOKEN_ENDPOINT
        #url_get_survey_data = Config.API_GATEWAY_AGGREGATED_SURVEYS_URL + 'todo/' + party_id
        url_get_survey_data = Config.RAS_AGGREGATOR_TODO.format(Config.RAS_API_GATEWAY_SERVICE, party_id)

        mock_object.post(url_get_token, status_code=200, json=returned_token)
        mock_object.get(url_get_survey_data, status_code=200, json=my_surveys_data)

        response = self.app.post('/sign-in/', data={'username': 'testuser@email.com', 'password': 'password'}, headers=self.headers)

        # Our system should check the response data.
        self.assertEqual(response.status_code, 302)
        self.assertTrue(bytes('You should be redirected automatically to target URL', encoding='UTF-8') in response.data)

        # TODO: this test was disabled - doesn't seem to work (GB/LB)

        response = self.app.get('/surveys/', data={}, headers=self.headers)

        # There should be the correct tabs
        self.assertTrue(bytes('SURVEY_TODO_TAB', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('SURVEY_HISTORY_TAB', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('SURVEY_MESSAGES_TAB', encoding='UTF-8') in response.data)

        # There should be the correct column headings
        self.assertTrue(bytes('SURVEY_COLUMN_HEADING', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('PERIOD_COVERED_COLUMN_HEADING', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('SUBMIT_BY_COLUMN_HEADING', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('STATUS_COLUMN_HEADING', encoding='UTF-8') in response.data)

        # There should be the correct data in the table row
        self.assertTrue(bytes(my_surveys_data['rows'][0]['businessData']['businessRef'], encoding='UTF-8') in response.data)
        self.assertTrue(bytes(my_surveys_data['rows'][0]['surveyData']['longName'], encoding='UTF-8') in response.data)
        self.assertTrue(bytes(my_surveys_data['rows'][0]['businessData']['name'], encoding='UTF-8') in response.data)
        self.assertTrue(bytes(my_surveys_data['rows'][0]['businessData']['businessRef'], encoding='UTF-8') in response.data)

        # TODO Check the status
        self.assertTrue(bytes(my_surveys_data['rows'][0]['status'], encoding='UTF-8') in response.data.lower())
        self.assertTrue(bytes('Not started', encoding='UTF-8') in response.data)

        # There should be Access Survey buttons
        self.assertTrue(bytes('ACCESS_SURVEY_BUTTON_1', encoding='UTF-8') in response.data)
        self.assertFalse(bytes('ACCESS_SURVEY_BUTTON_2', encoding='UTF-8') in response.data)

    # Test the Access Survey page
    @requests_mock.mock()
    def test_access_survey_page(self, mock_object):
        """Test we display survey data after signing in correctly"""

        # Build mock URL's which are used to provide application data
        url_get_token = Config.ONS_OAUTH_PROTOCOL + Config.ONS_OAUTH_SERVER + Config.ONS_TOKEN_ENDPOINT
        #url_get_survey_data = Config.API_GATEWAY_AGGREGATED_SURVEYS_URL + 'todo/' + party_id
        url_get_survey_data = Config.RAS_AGGREGATOR_TODO.format(Config.RAS_API_GATEWAY_SERVICE, party_id)

        #url_get_collection_instrument_data = Config.API_GATEWAY_COLLECTION_INSTRUMENT_URL + 'collectioninstrument/id/' + collection_instrument_id
        url_get_collection_instrument_data = Config.RAS_CI_GET.format(Config.RAS_COLLECTION_INSTRUMENT_SERVICE, collection_instrument_id)

        url_get_cases = Config.RM_CASE_GET_BY_PARTY.format(Config.RM_CASE_SERVICE, party_id)

        mock_object.post(url_get_token, status_code=200, json=returned_token)
        mock_object.get(url_get_survey_data, status_code=200, json=my_surveys_data)
        mock_object.get(url_get_collection_instrument_data, status_code=200, json=collection_instrument_data)
        mock_object.get(url_get_cases, status_code=200, json=cases_data)
        print("Cases>", url_get_cases)

        self.app.post('/sign-in/', data={'username': 'testuser@email.com', 'password': 'password'}, headers=self.headers)

        survey_params = {
            'case_id': case_id,
            'collection_instrument_id': collection_instrument_id
        }

        response = self.app.post('/surveys/access_survey', headers=self.headers, data=survey_params)
        self.assertEqual(response.status_code, 200)

        # There should be a Download button
        self.assertTrue(bytes('download-survey-button', encoding='UTF-8') in response.data)

        # There should be an Upload button
        self.assertTrue(bytes('upload-survey-button', encoding='UTF-8') in response.data)
