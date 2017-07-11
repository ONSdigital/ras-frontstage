import unittest
from app.application import app
from app.config import Config
import json
import requests_mock
from ons_ras_common import ons_env

with open('tests/test_data/my_surveys.json') as json_data:
    my_surveys_data = json.load(json_data)

returned_token = {
    "id": 6,
    "access_token": "a712f0f9-d00d-447a-b143-49984ca3db68",
    "expires_in": 3600,
    "token_type": "Bearer",
    "scope": "",
    "refresh_token": "37ca04d2-6b6c-4854-8e85-f59c2cc7d3de"
}

party_id = '3b136c4b-7a14-4904-9e01-13364dd7b972'
enrolment_code = 'ABCDEF123456'
encrypted_enrolment_code = 'WfwJghohWOZTIYnutlTcVucqnuED5Lm9q8t0L4ASHPo='
case_id = "7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb"

test_user = {
    'first_name': 'john',
    'last_name': 'doe',
    'email_address': 'testuser2@email.com',
    'password': 'password',
    'password_confirm': 'password',
    'phone_number': '07717275049'
}


class TestRegistration(unittest.TestCase):
    """Test case for application endpoints and functionality"""

    def setUp(self):

        self.app = app.test_client()
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
            }

    # ============== CREATE ACCOUNT (ENTER ENROLMENT CODE) ===============

    # Test the Enter Enrolment Code page
    @requests_mock.mock()
    def test_enter_enrolment_code_page(self, mock_object):

        # GET the Create Account (Enter Enrolment Code) page
        response = self.app.get('/create-account/', headers=self.headers)

        # Check successful response and the correct values are on the page
        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes('Create an account', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('Enrolment Code', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('You\'ll find this in the letter we sent you', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('CONTINUE_BUTTON', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('sign in here', encoding='UTF-8') in response.data)

        # Build the URL and that is used to validate the IAC
        url_validate_iac = Config.API_GATEWAY_IAC_URL + '{}'.format(enrolment_code)

        iac_response = {
            "iac": enrolment_code,
            "active": True,
            "lastUsedDateTime": "2017-05-15T10:00:00Z",
            "caseId": case_id,
            "questionSet": "H1"
        }

        # Mock the IAC service to validate the enrolment code
        mock_object.get(url_validate_iac, status_code=200, json=iac_response)
        
        # Mock the post event service
        def my_post_event(*args, **kwargs):
            print('Called POST EVENT service with args={},kwargs={}'.format(str(args), str(kwargs)))
        ons_env.case_service.post_event = my_post_event

        # Enrolment code post data
        post_data = {
            'enrolment_code': 'ABCDEF123456'
        }

        # POST to the Create Account (Enter Enrolment Code) page
        response = self.app.post('/create-account/', data=post_data, headers=self.headers)

        # After a successful POST the user should be redirected to the Confirm Org screen
        self.assertEqual(response.status_code, 302)
        self.assertTrue(bytes('You should be redirected automatically to target URL', encoding='UTF-8') in response.data)
        self.assertTrue(
            bytes('/create-account/confirm-organisation-survey/?enrolment_code=', encoding='UTF-8') in response.data)

    # ============== CONFIRM ORG AND SURVEY ===============
    @requests_mock.mock()
    def test_confirm_org_page(self, mock_object):
        # TODO Check that the correct details are on the screen
        # self.assertTrue(bytes('Enrolment code', encoding='UTF-8') in response.data)
        # self.assertTrue(bytes('Organisation', encoding='UTF-8') in response.data)
        # self.assertTrue(bytes('Survey to complete', encoding='UTF-8') in response.data)
        # self.assertTrue(bytes('CONFIRM_AND_CONTINUE_BUTTON', encoding='UTF-8') in response.data)
        self

    @requests_mock.mock()
    def test_confirm_org_page_inactive_enrolment_code(self, mock_object):
        # TODO Check that the error page is displayed if the user has not passed in an active encrypted enrolment code
        # self.assertTrue('/error'.encode() in response.data)
        self

    # ============== ENTER YOUR ACCOUNT DETAILS ===============

    # Trying to access the enter account details page with a valid encrypted active enrolment code should
    # result in the page being displayed
    @requests_mock.mock()
    def test_create_account_get_page_with_active_enrolment_code(self, mock_object):

        url_validate_active_iac = Config.API_GATEWAY_IAC_URL + '{}'.format(enrolment_code)
        iac_active_response = {
            "iac": enrolment_code,
            "active": True,
            "lastUsedDateTime": "2017-05-15T10:00:00Z",
            "caseId": case_id,
            "questionSet": "H1"
        }
        mock_object.get(url_validate_active_iac, status_code=200, json=iac_active_response)

        # A GET with a valid, active enrolment code should result in the page being displayed
        params = {
            'enrolment_code': encrypted_enrolment_code,
            'organisation_name': 'Bolts and Ratchets Ltd',
            'survey_name': 'Business Register and Employment Survey'
        }

        # 'enrolment_code=mQsp74%2F%2BrFxONgwWgrDWWp%2BSrDQsSi1h6ZBNGbkOEXk%3D&organisation_name=Bolts+and+Ratchets+Ltd&survey_name=Business+Register+and+Employment+Survey'
        response = self.app.get('/create-account/enter-account-details', query_string=params, headers=self.headers)
        self.assertEqual(response.status_code, 200)

        # Check that the correct details are displayed on the screen after it is successfully accessed
        self.assertTrue(bytes('Enter your account details', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('Your name', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('Email address', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('Create a password', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('Phone number', encoding='UTF-8') in response.data)

    # Trying to access the enter account details page with a invalid encrypted (inactive) enrolment code should
    # result in the error page being displayed
    @requests_mock.mock()
    def test_create_account_get_page_with_inactive_enrolment_code(self, mock_object):

        url_validate_inactive_iac = Config.API_GATEWAY_IAC_URL + '{}'.format(enrolment_code)
        iac_inactive_response = {
            "iac": enrolment_code,
            "active": False,
            "lastUsedDateTime": "2017-05-15T10:00:00Z",
            "caseId": case_id,
            "questionSet": "H1"
        }
        mock_object.get(url_validate_inactive_iac, status_code=200, json=iac_inactive_response)

        post_data = {
            'enrolment_code': encrypted_enrolment_code
        }

        # A POST with an invalid or inactive enrolment code should result in an error
        response = self.app.post('/create-account/enter-account-details', data=post_data, headers=self.headers)
        # self.assertTrue(response.status_code, 200)
        # self.assertTrue('/error'.encode() in response.data)

    # Trying to access the enter account details page without an enrolment code should
    # result in the error page
    @requests_mock.mock()
    def test_create_account_get_page_without_enrolment_code(self, mock_object):
        """Test create account page is not rendered for an invalid get request"""

        # Build the URL and that is used to validate the IAC
        url_validate_no_iac = Config.API_GATEWAY_IAC_URL + '{}'.format(None)
        no_iac_response = {

        }
        mock_object.get(url_validate_no_iac, status_code=200, json=no_iac_response)

        # A GET with no enrolment code should result in an error
        response = self.app.get('/create-account/enter-account-details', headers=self.headers)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/error'.encode() in response.data)

    # TODO Fix this test as part of the 'enter your account details' story
    ###############################################################################################################
    ######### The tests below now require a valid, active encrypted enrolment code to be passed into the page, ########
    ######### otherwise the user redirects off to the error page ##################################################
    #
    # def test_create_account_register_no_email_address(self):
    #     """Test create account with no email address responds with field required"""
    #
    #     # creating user
    #     another_test_user = {
    #         'first_name': 'john',
    #         'last_name': 'doe'
    #     }
    #
    #     response = self.app.post('create-account/enter-account-details/', data=another_test_user, headers=self.headers)
    #
    #     self.assertTrue(response.status_code, 200)
    #     self.assertTrue(bytes('This field is required', encoding='UTF-8') in response.data)

    # TODO Fix this test as part of the 'enter your account details' story
    # def test_create_account_register_no_password(self):
    #     """Test create account with no password returns response field required"""
    #
    #     # creating user
    #     another_test_user = {
    #         'first_name': 'john',
    #         'last_name': 'doe',
    #         'email_address': 'testuser2@email.com',
    #         'email_address_confirm': 'wrongemailaddres@email.com'
    #     }
    #
    #     response = self.app.post('create-account/enter-account-details/', data=another_test_user, headers=self.headers)
    #
    #     self.assertTrue(response.status_code, 200)
    #     self.assertTrue(bytes('This field is required', encoding='UTF-8') in response.data)

    # TODO Fix this test as part of the 'enter your account details' story
    # def test_create_account_register_wrong_password(self):
    #     """Test create account with mismatching passwords returns passwords must match"""
    #
    #     # creating user
    #     another_test_user = {
    #         'first_name': 'john',
    #         'last_name': 'doe',
    #         'email_address': 'testuser2@email.com',
    #         'password': 'password',
    #         'password_confirm': 'wrongpassword'
    #     }
    #
    #     response = self.app.post('create-account/enter-account-details/', data=another_test_user, headers=self.headers)
    #
    #     self.assertTrue(response.status_code, 200)
    #     self.assertTrue(bytes('Passwords must match', encoding='UTF-8') in response.data)

    # TODO Fix this test as part of the 'enter your account details' story
    # def test_create_account_register_no_phone_number(self):
    #     """Test create account missing phone no. returns field required"""
    #
    #     # creating user
    #     another_test_user = {
    #         'first_name': 'john',
    #         'last_name': 'doe',
    #         'email_address': 'testuser2@email.com',
    #         'password': 'password1234',
    #         'password_confirm': 'password1234'
    #     }
    #
    #     response = self.app.post('create-account/enter-account-details/', data=another_test_user, headers=self.headers)
    #
    #     self.assertTrue(response.status_code, 200)
    #     self.assertTrue(bytes('This field is required.', encoding='UTF-8') in response.data)

    # TODO Fix this test as part of the 'enter your account details' story
    # def test_create_account_register_illegal_phone_number(self):
    #     """Test create account with an invalid phone no. returns not a valid UK phone no."""
    #
    #     # creating user
    #     another_test_user = {
    #         'first_name': 'john',
    #         'last_name': 'doe',
    #         'email_address': 'testuser2@email.com',
    #         'password': 'password1234',
    #         'password_confirm': 'password1234',
    #         'phone_number': 'not a number'
    #     }
    #
    #     response = self.app.post('create-account/enter-account-details/', data=another_test_user, headers=self.headers)
    #
    #     self.assertTrue(response.status_code, 200)
    #     self.assertTrue(bytes('This should be a valid UK number e.g. 01632 496 0018', encoding='UTF-8') in response.data)

    # TODO Fix this test as part of the 'enter your account details' story
    # def test_create_account_register_phone_number_too_small(self):
    #     """Test create account phone no. too small returns length guidance"""
    #
    #     # creating user
    #     another_test_user = {
    #         'first_name': 'john',
    #         'last_name': 'doe',
    #         'email_address': 'testuser2@email.com',
    #         'password': 'password1234',
    #         'password_confirm': 'password1234',
    #         'phone_number': '12345678'
    #     }
    #
    #     response = self.app.post('create-account/enter-account-details/', data=another_test_user, headers=self.headers)
    #
    #     self.assertTrue(response.status_code, 200)
    #     self.assertTrue(bytes('This should be a valid phone number between 9 and 15 digits', encoding='UTF-8') in response.data)

    # TODO Fix this test as part of the 'enter your account details' story
    # def test_create_account_register_phone_number_too_big(self):
    #     """Test create account phone no. too big returns length guidance"""
    #
    #     # creating user
    #     another_test_user = {
    #         'first_name': 'john',
    #         'last_name': 'doe',
    #         'email_address': 'testuser2@email.com',
    #         'password': 'password1234',
    #         'password_confirm': 'password1234',
    #         'phone_number': '1234567890123456'
    #     }
    #
    #     response = self.app.post('create-account/enter-account-details/', data=another_test_user, headers=self.headers)
    #
    #     self.assertTrue(response.status_code, 200)
    #     self.assertTrue(bytes('This should be a valid phone number between 9 and 15 digits', encoding='UTF-8') in response.data)

    # TODO Fix this test as part of the 'enter your account details' story
    # @requests_mock.mock()
    # def test_create_account_register_new_user(self, mock_object):
    #     """Test successful create account"""
    #
    #     # Build URL's which is used to talk to the OAuth2 server
    #     url_create_user = OAuthConfig.ONS_OAUTH_PROTOCOL + OAuthConfig.ONS_OAUTH_SERVER + OAuthConfig.ONS_ADMIN_ENDPOINT
    #     url_get_token = OAuthConfig.ONS_OAUTH_PROTOCOL + OAuthConfig.ONS_OAUTH_SERVER + OAuthConfig.ONS_TOKEN_ENDPOINT
    #     url_get_survey_data = Config.API_GATEWAY_PARTY_URL + 'respondents'
    #
    #     # Here we place a listener on the URL's The flow of events are:
    #     # 1) The ras_frontstage creates a user on the OAuth2 server.
    #     # 2) The OAuth2 replies with a HTTP 200 OK.
    #     # 3) The ras_frontstage requests a client Token from the OAuth2 to allow it to speak with the PartyServer.
    #     # 4) The OAuth2 sends a token, refresh token, TTL and scopes.
    #     # 5) The ras_frontstage requests survey data from the Party Service.
    #     # 6) The Party Servie replys with survey data.
    #     # This means we need to mock 2) 4) and  6)
    #     #
    #     mock_object.post(url_create_user, status_code=200, json={"account": "testuser2@email.com", "created": "success"})
    #     mock_object.post(url_get_token, status_code=200, json=returned_token)
    #     mock_object.post(url_get_survey_data, status_code=200, json=my_surveys_data)
    #
    #     response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)
    #
    #     self.assertTrue(response.status_code, 301)
    #     self.assertTrue(bytes('Please follow the link in the email to confirm your email address and finish setting up your account.',
    #                           encoding='UTF-8') in response.data)

    # TODO Fix this test as part of the 'enter your account details' story
        
    # Test we present the user with a page to say this email is already in use when we register the same user twice.
    # We are using the requests_mock library to fake the call to an OAuth2 server and the party service.
    # See: https://requests-mock.readthedocs.io/en/latest/response.html
    # @requests_mock.mock()
    # def test_create_duplicate_account(self, mock_object):
    #     """Test create a duplicate account returns 'try a different email this ones in use' """
    #
    #     # Build URL's which is used to talk to the OAuth2 server
    #     url_create_user = OAuthConfig.ONS_OAUTH_PROTOCOL + OAuthConfig.ONS_OAUTH_SERVER + OAuthConfig.ONS_ADMIN_ENDPOINT
    #
    #     # Here we place a listener on this URL. This is the URL of the OAuth2 server. We send a 401 to reject the request
    #     # from the ras_frontstage to get a token for this user. See application.py login()
    #
    #     mock_object.post(url_create_user, status_code=401, json={"detail": "Duplicate user credentials"})
    #
    #     response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)
    #
    #     self.assertTrue(response.status_code, 200)
    #     self.assertTrue(bytes('Please try a different email, this one is in use', encoding='UTF-8') in response.data)
