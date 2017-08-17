import json
import unittest

import requests_mock
from ons_ras_common import ons_env

from frontstage import app


with open('tests/test_data/my_surveys.json') as json_data:
    my_surveys_data = json.load(json_data)

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

# Build the URL and that is used to validate the IAC
url_validate_iac = app.config['API_GATEWAY_IAC_URL'] + '{}'.format(enrolment_code)

url_validate_iac = app.config['RM_IAC_GET'].format(app.config['RM_IAC_SERVICE'], enrolment_code)


params = {
    "enrolment_code": encrypted_enrolment_code
}


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

    # Test the Enter Enrolment Code page
    @requests_mock.mock()
    def test_enter_enrolment_code_page(self, mock_object):
        # GET the Create Account (Enter Enrolment Code) page
        response = self.app.get('/register/create-account/', headers=self.headers)

        # Check successful response and the correct values are on the page
        self.assertEqual(response.status_code, 200)

    # ============== CONFIRM ORG AND SURVEY ===============
    @requests_mock.mock()
    def test_confirm_org_page(self, mock_object):

        # Multiple GET requests are made on this page so all need to be mocked with the correct data response
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)
        url_get_case = app.config['RM_CASE_GET'].format(app.config['RM_CASE_SERVICE'], case_id)
        mock_object.get(url_get_case, status_code=200, json=case_json)

        business_party_id = case_json['caseGroup']['partyId']
        url_get_party = app.config['RAS_PARTY_GET_BY_BUSINESS'].format(app.config['RAS_PARTY_SERVICE'], party_id)
        mock_object.get(url_get_party, status_code=200, json=party_json)

        collection_exercise_id = case_json['caseGroup']['collectionExerciseId']
        url_get_coll = app.config['RM_COLLECTION_EXERCISES_GET'].format(app.config['RM_COLLECTION_EXERCISE_SERVICE'], collection_exercise_id)
        mock_object.get(url_get_coll, status_code=200, json=coll_json)

        survey_id = coll_json['surveyId']
        url_get_survey = app.config['RM_SURVEY_GET'].format(app.config['RM_SURVEY_SERVICE'], survey_id)
        mock_object.get(url_get_survey, status_code=200, json=survey_json)

        # A GET request with the correct enrolment codes should bring up the page
        response = self.app.get('/register/create-account/confirm-organisation-survey/', query_string=params, headers=self.headers, follow_redirects=True)

        # Check that the correct details are displayed on the screen after it is successfully accessed
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Confirm organisation'.encode() in response.data)

    @requests_mock.mock()
    def test_confirm_org_page_inactive_enrolment_code(self, mock_object):

        # Setting enrolment code to inactive
        self.iac_response['active'] = False
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)

        # A POST with an invalid or inactive enrolment code should result in an error page being displayed
        response = self.app.get('/register/create-account/confirm-organisation-survey/', query_string=params, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Oops!'.encode() in response.data)

    # ============== ENTER YOUR ACCOUNT DETAILS ===============
    @requests_mock.mock()
    def test_create_account_get_page_with_active_enrolment_code(self, mock_object):

        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)

        # A GET with a valid, active enrolment code should result in the page being displayed
        response = self.app.get('/register/create-account/enter-account-details', query_string=params, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('send you an email'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_get_page_with_inactive_enrolment_code(self, mock_object):

        # Setting enrolment code to inactive
        self.iac_response['active'] = False
        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)

        # A GET with a valid, inactive enrolment code should result in the error page being displayed
        response = self.app.get('/register/create-account/enter-account-details', query_string=params, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Oops!'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_get_page_without_enrolment_code(self, mock_object):
        """Test create account page is not rendered for an invalid get request"""

        # A GET with no enrolment code should result in the error page being displayed
        response = self.app.get('/register/create-account/enter-account-details', headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Oops!'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_no_email_address(self, mock_object):
        """Test create account with no email address responds with field required"""

        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)

        # deleting user email
        del self.test_user['email_address']

        # A POST with no email should prompt the user
        self.headers['referer'] = '/register/create-account/enter-account-details'
        response = self.app.post('/register/create-account/enter-account-details', query_string=params, data=self.test_user, headers=self.headers, follow_redirects=True)

        # Check that the correct details are displayed on the screen after it is successfully accessed
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Enter your account details'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_no_password(self, mock_object):
        """Test create account with no password returns response field required"""

        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)

        # deleting user passwords
        del self.test_user['password']
        del self.test_user['password_confirm']

        # A POST with no password should prompt the user
        self.headers['referer'] = 'register/create-account/enter-account-details'
        response = self.app.post('register/create-account/enter-account-details', query_string=params, data=self.test_user, headers=self.headers, follow_redirects=True)

        # Check that the correct details are displayed on the screen after it is successfully accessed
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please check the passwords'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_wrong_password(self, mock_object):
        """Test create account with mismatching passwords returns passwords must match"""

        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)

        # changing user password confirm
        self.test_user['password_confirm'] = 'wrongpassword'

        # A POST with non-matching passwords should prompt the user
        self.headers['referer'] = 'register/create-account/enter-account-details'
        response = self.app.post('register/create-account/enter-account-details', query_string=params, data=self.test_user, headers=self.headers, follow_redirects=True)

        # Check that the correct details are displayed on the screen after it is successfully accessed
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please check the passwords'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_no_phone_number(self, mock_object):
        """Test create account missing phone no. returns field required"""

        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)

        # deleting user telephone number
        del self.test_user['phone_number']

        # A POST with no phone number should prompt the user
        self.headers['referer'] = 'register/create-account/enter-account-details'
        response = self.app.post('register/create-account/enter-account-details', query_string=params, data=self.test_user, headers=self.headers, follow_redirects=True)

        # Check that the correct details are displayed on the screen after it is successfully accessed
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please check the phone number'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_illegal_phone_number(self, mock_object):
        """Test create account with an invalid phone no. returns not a valid UK phone no."""

        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)

        # changing user phone number
        self.test_user['phone_number'] = 'not a number'

        # A POST with an invalid phone number should prompt the user
        self.headers['referer'] = 'register/create-account/enter-account-details'
        response = self.app.post('register/create-account/enter-account-details', query_string=params, data=self.test_user, headers=self.headers, follow_redirects=True)

        # Check that the correct details are displayed on the screen after it is successfully accessed
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please check the phone number'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_phone_number_too_small(self, mock_object):
        """Test create account phone no. too small returns length guidance"""

        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)

        # changing user phone number
        self.test_user['phone_number'] = '12345678'

        # A POST with an invalid phone number should prompt the user
        self.headers['referer'] = 'register/create-account/enter-account-details'
        response = self.app.post('register/create-account/enter-account-details', query_string=params, data=self.test_user, headers=self.headers, follow_redirects=True)

        # Check that the correct details are displayed on the screen after it is successfully accessed
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please check the phone number'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_phone_number_too_big(self, mock_object):
        """Test create account phone no. too big returns length guidance"""

        mock_object.get(url_validate_iac, status_code=200, json=self.iac_response)

        # changing user phone number
        self.test_user['phone_number'] = '1234567890123456'

        # A POST with an invalid phone number should prompt the user
        self.headers['referer'] = 'register/create-account/enter-account-details'
        response = self.app.post('register/create-account/enter-account-details', query_string=params, data=self.test_user, headers=self.headers, follow_redirects=True)

        # Check that the correct details are displayed on the screen after it is successfully accessed
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please check the phone number'.encode() in response.data)
