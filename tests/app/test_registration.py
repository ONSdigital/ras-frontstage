import json
import unittest

import requests_mock

from frontstage import app


with open('tests/test_data/my_surveys.json') as json_data:
    my_surveys_data = json.load(json_data)
with open('tests/test_data/case_categories.json') as json_data:
    categories_data = json.load(json_data)

returned_token = {
    "id": 6,
    "access_token": "a712f0f9-d00d-447a-b143-49984ca3db68",
    "expires_in": 3600,
    "token_type": "Bearer",
    "scope": "",
    "refresh_token": "37ca04d2-6b6c-4854-8e85-f59c2cc7d3de",
    "party_id": "3b136c4b-7a14-4904-9e01-13364dd7b972"

}

party_id = '3b136c4b-7a14-4904-9e01-13364dd7b972'
enrolment_code = 'ABCDEF123456'
encrypted_enrolment_code = 'WfwJghohWOZTIYnutlTcVucqnuED5Lm9q8t0L4ASHPo='
case_id = "7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb"

# These json objects only contain the key-value pairs required for testing
case_json = {
    "caseGroup": {
        "collectionExerciseId": "c6467711-21eb-4e78-804c-1db8392f93fb",
        "partyId": "3b136c4b-7a14-4904-9e01-13364dd7b972"
    }
}

case_iac_json = {
    "collectionExerciseId": "c6467711-21eb-4e78-804c-1db8392f93fb",
    "partyId": "3b136c4b-7a14-4904-9e01-13364dd7b972"
}

party_json = {
  "name": "Bolts and Ratchets Ltd"
}

coll_json = {
    "surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"
}

survey_json = {
  "id": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87",
  "longName": "Business Register and Employment Survey",
  "shortName": "BRES"
}
params = {
    "enrolment_code": encrypted_enrolment_code
}
oauth_token = {
    "id": 503,
    "access_token": "8c77e013-d8dc-472c-b4d3-d4fbe21f80e7",
    "expires_in": 3600,
    "token_type": "Bearer",
    "scope": "",
    "refresh_token": "b7ac07a6-4c28-43bd-a335-00250b490e9f"
}

url_validate_iac = app.config['RM_IAC_GET'].format(app.config['RM_IAC_SERVICE'], enrolment_code)
url_case_from_iac = app.config['RM_CASE_GET_BY_IAC'].format(app.config['RM_CASE_SERVICE'], enrolment_code)
url_case_categories = '{}categories'.format(app.config['RM_CASE_SERVICE'])
url_case_post = '{}cases/{}/events'.format(app.config['RM_CASE_SERVICE'], case_id)
url_get_case = app.config['RM_CASE_GET'].format(app.config['RM_CASE_SERVICE'], case_id)
url_get_party = app.config['RAS_PARTY_GET_BY_BUSINESS'].format(app.config['RAS_PARTY_SERVICE'], party_id)
collection_exercise_id = case_json['caseGroup']['collectionExerciseId']
url_get_coll = app.config['RM_COLLECTION_EXERCISES_GET'].format(app.config['RM_COLLECTION_EXERCISE_SERVICE'],
                                                                collection_exercise_id)
survey_id = coll_json['surveyId']
url_get_survey = app.config['RM_SURVEY_GET'].format(app.config['RM_SURVEY_SERVICE'], survey_id)
url_oauth_token = app.config['ONS_TOKEN']
url_create_party = app.config['RAS_PARTY_POST_RESPONDENTS'].format(app.config['RAS_PARTY_SERVICE'])


class TestRegistration(unittest.TestCase):
    """Test case for application endpoints and functionality"""

    def setUp(self):

        self.app = app.test_client()
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
            }
        self.test_user = {
            'first_name': 'john',
            'last_name': 'doe',
            'email_address': 'testuser2@email.com',
            'password': 'Password123!',
            'password_confirm': 'Password123!',
            'phone_number': '07717275049'
            }
        self.iac_response = {
            "iac": enrolment_code,
            "active": True,
            "lastUsedDateTime": "2017-05-15T10:00:00Z",
            "caseId": case_id,
            "questionSet": "H1"
            }

    # ============== CREATE ACCOUNT (ENTER ENROLMENT CODE) ===============
    def test_view_enrolment_code_page(self):
        response = self.app.get('/register/create-account')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Create an account'.encode() in response.data)
        self.assertTrue('Enrolment Code'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_enrolment_code(self, mock_object):
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)
        mock_object.get(url_case_from_iac, status_code=200, json=case_iac_json)
        mock_object.get(url_case_categories, status_code=200, json=categories_data)
        mock_object.post(url_case_post, status_code=201)

        response = self.app.post('/register/create-account', data={'enrolment_code': enrolment_code})

        self.assertEqual(response.status_code, 302)
        self.assertTrue('confirm-organisation-survey'.encode() in response.data)

    def test_no_enrolment_code(self):
        response = self.app.post('/register/create-account')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Create an account'.encode() in response.data)
        ##### No specific error message shown for this currently #####

    @requests_mock.mock()
    def test_unrecognised_enrolment_code(self, mock_object):
        mock_object.get(url_validate_iac, status_code=404, json=self.iac_response)

        response = self.app.post('/register/create-account', data={'enrolment_code': enrolment_code})

        self.assertEqual(response.status_code, 202)
        self.assertTrue('Enrolment code not valid'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_enrolment_code_case_fail(self, mock_object):
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)
        mock_object.get(url_case_from_iac, status_code=500, json=case_iac_json)

        response = self.app.post('/register/create-account',
                                 data={'enrolment_code': enrolment_code},
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_enrolment_code_case_post_fail(self, mock_object):
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)
        mock_object.get(url_case_from_iac, status_code=200, json=case_iac_json)
        mock_object.get(url_case_categories, status_code=200, json=categories_data)
        mock_object.post(url_case_post, status_code=500)

        response = self.app.post('/register/create-account',
                                 data={'enrolment_code': enrolment_code})

        self.assertEqual(response.status_code, 302)
        self.assertTrue('confirm-organisation-survey'.encode() in response.data)

    # ============== CONFIRM ORG AND SURVEY ===============
    @requests_mock.mock()
    def test_confirm_org_page(self, mock_object):
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)
        mock_object.get(url_get_case, status_code=200, json=case_json)
        mock_object.get(url_get_party, status_code=200, json=party_json)
        mock_object.get(url_get_coll, status_code=200, json=coll_json)
        mock_object.get(url_get_survey, status_code=200, json=survey_json)

        response = self.app.get('/register/create-account/confirm-organisation-survey',
                                query_string=params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Confirm organisation'.encode() in response.data)

    @requests_mock.mock()
    def test_confirm_org_page_inactive_enrolment_code(self, mock_object):
        self.iac_response['active'] = False
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)

        response = self.app.get('/register/create-account/confirm-organisation-survey',
                                query_string=params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Oops!'.encode() in response.data)

    # ============== ENTER YOUR ACCOUNT DETAILS ===============
    @requests_mock.mock()
    def test_create_account_get_page_with_active_enrolment_code(self, mock_object):
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)

        response = self.app.get('/register/create-account/enter-account-details',
                                query_string=params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('send you an email'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_get_page_with_inactive_enrolment_code(self, mock_object):
        self.iac_response['active'] = False
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)

        response = self.app.get('/register/create-account/enter-account-details',
                                query_string=params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Oops!'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_get_page_without_enrolment_code(self, mock_object):
        """Test create account page is not rendered for an invalid get request"""
        response = self.app.get('/register/create-account/enter-account-details',
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Oops!'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_no_email_address(self, mock_object):
        """Test create account with no email address responds with field required"""
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)
        del self.test_user['email_address']
        self.headers['referer'] = '/register/create-account/enter-account-details'

        response = self.app.post('/register/create-account/enter-account-details',
                                 query_string=params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Enter your account details'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_no_password(self, mock_object):
        """Test create account with no password returns response field required"""
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)
        del self.test_user['password']
        del self.test_user['password_confirm']
        self.headers['referer'] = 'register/create-account/enter-account-details'

        response = self.app.post('register/create-account/enter-account-details',
                                 query_string=params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please check the passwords'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_wrong_password(self, mock_object):
        """Test create account with mismatching passwords returns passwords must match"""
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)
        self.test_user['password_confirm'] = 'wrongpassword'
        self.headers['referer'] = 'register/create-account/enter-account-details'

        response = self.app.post('register/create-account/enter-account-details',
                                 query_string=params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please check the passwords'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_no_phone_number(self, mock_object):
        """Test create account missing phone no. returns field required"""
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)
        del self.test_user['phone_number']
        self.headers['referer'] = 'register/create-account/enter-account-details'

        response = self.app.post('register/create-account/enter-account-details',
                                 query_string=params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please check the phone number'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_illegal_phone_number(self, mock_object):
        """Test create account with an invalid phone no. returns not a valid UK phone no."""
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)
        self.test_user['phone_number'] = 'not a number'
        self.headers['referer'] = 'register/create-account/enter-account-details'

        response = self.app.post('register/create-account/enter-account-details',
                                 query_string=params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please check the phone number'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_phone_number_too_small(self, mock_object):
        """Test create account phone no. too small returns length guidance"""
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)
        self.test_user['phone_number'] = '12345678'
        self.headers['referer'] = 'register/create-account/enter-account-details'

        response = self.app.post('register/create-account/enter-account-details',
                                 query_string=params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please check the phone number'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_phone_number_too_big(self, mock_object):
        """Test create account phone no. too big returns length guidance"""
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)
        self.test_user['phone_number'] = '1234567890123456'
        self.headers['referer'] = 'register/create-account/enter-account-details'

        response = self.app.post('register/create-account/enter-account-details',
                                 query_string=params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please check the phone number'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_success(self, mock_object):
        """Test create account phone no. too big returns length guidance"""
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)
        mock_object.post(url_oauth_token, status_code=201, json=oauth_token)
        mock_object.post(url_create_party, status_code=200)
        self.headers['referer'] = 'register/create-account/enter-account-details'

        response = self.app.post('register/create-account/enter-account-details',
                                 query_string=params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Almost done'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_duplicate_email(self, mock_object):
        """Test create account phone no. too big returns length guidance"""
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)
        mock_object.post(url_oauth_token, status_code=201, json=oauth_token)
        mock_object.post(url_create_party, status_code=400)
        self.headers['referer'] = 'register/create-account/enter-account-details'

        response = self.app.post('register/create-account/enter-account-details',
                                 query_string=params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('This email has already been used'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_oauth_fail(self, mock_object):
        """Test create account phone no. too big returns length guidance"""
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)
        mock_object.post(url_oauth_token, status_code=401, json=oauth_token)
        mock_object.post(url_create_party, status_code=500)
        self.headers['referer'] = 'register/create-account/enter-account-details'

        response = self.app.post('register/create-account/enter-account-details',
                                 query_string=params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)
