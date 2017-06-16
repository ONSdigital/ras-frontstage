import unittest
from app.application import app
from app.jwt import encode, decode
from app.config import OAuthConfig
import requests_mock


data_dict_for_jwt_token = {"refresh_token": "eyJhbGciOiJIUzI1NiIsIn",
                           "access_token": "access_token",
                           "scope": "[foo,bar,qnx]",
                           "expires_at": "100123456789",
                           "username": "johndoe"}

data_dict_zero_length = {"": ""}

encoded_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NfdG9rZW4iOiJhY2Nlc3NfdG9rZW4iLCJzY29wZSI6Iltmb28sYmFyLHFueF0iLCJ1c2VybmFtZSI6ImpvaG5kb2UiLCJleHBpcmVzX2F0IjoiMTAwMTIzNDU2Nzg5IiwicmVmcmVzaF90b2tlbiI6ImV5SmhiR2NpT2lKSVV6STFOaUlzSW4ifQ.SIgs3BFhAaJS6s9Q6gm57o9ifVqgAh0AC7-jDigSLZo'


class TestApplication(unittest.TestCase):
    """Test case for application endpoints and functionality"""

    def setUp(self):

        self.app = app.test_client()
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
            }

    # Test we can encode a token with the format shown in data_dict_for_jwt_token
    def test_encode_jwt(self):

        self.assertEqual(encode(data_dict_for_jwt_token), encoded_token)

    # Test we get an error when our token is zero length
    def test_encode_bad_data(self):

        self.assertEqual(encode(data_dict_zero_length), 'No data')

    # TODO Test that over a certain size our encode returns the correct error and handles gracefully

    # Test that we can decode our token
    def test_decode_jwt(self):

        self.assertEqual(decode(encoded_token), data_dict_for_jwt_token)

    # By passing a correct token this function should get a HTTP 200
    # data={"error": {"type": "success"}}
    def test_logged_in(self):
        "Testing Logged In"
        response = self.app.get('logged-in', headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes('Error! You are not logged in!', encoding='UTF-8') in response.data)

    # By passing an incorrect token this function should get an HTTP 200 with a data dictionary  type set as failed
    # data={"error": {"type": "failed"}}

    def test_sign_in_page(self):
        """Test user sign in appears"""

        response = self.app.get('/sign-in', headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Sign in', response.data)
        self.assertTrue('Email Address', response.data)
        self.assertTrue('Password', response.data)

    # Test we get an incorrect email or password message when a user who does not exist on the OAuth2 server sign's in
    # We are using the requests_mock library to fake the call to an OAuth2 server. See: https://requests-mock.readthedocs.io/en/latest/response.html
    @requests_mock.mock()
    def test_sign_in_wrong_details(self, mock_object):
        """Test incorrect detail message is returned with invalid details entered"""
        # data = {'refresh_token': '007', 'access_token': '007', 'scope': '[foo,bar]', 'expires_at': 'today', 'username': 'nherriot' }
        url = OAuthConfig.ONS_OAUTH_PROTOCOL + OAuthConfig.ONS_OAUTH_SERVER + OAuthConfig.ONS_TOKEN_ENDPOINT
        # m.post('http://localhost:8000/api/v1/tokens/', status_code=401, text=str(data))

        # Here we place a listener on this URL. This is the URL of the OAuth2 server. We send a 401 to reject the request
        # from the ras_frontstage to get a token for this user. See application.py login(). And the call to oauth.fetch_token
        mock_object.post(url, status_code=401, json={'detail': 'Unauthorized user credentials'})

        # Lets send a post message to the ras_frontstage at the endpoint /sign-in/OAuth.
        response = self.app.post('/sign-in/OAuth', data={'username': 'test', 'password': 'test'}, headers=self.headers)

        # Our system should still handle this.
        self.assertEqual(response.status_code, 200)

        # Check this guy has an incorrect email.
        self.assertTrue(bytes('Incorrect email or password', encoding='UTF-8') in response.data)

        self.assertTrue(bytes('Sign in', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('Email Address', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('Password', encoding='UTF-8') in response.data)

    def test_create_account_get_page(self):
        """Test create account page is rendered for a get request"""

        response = self.app.get('create-account/enter-account-details/', headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue(bytes('Enter your account details', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('Your name', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('Email address', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('Create a password', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('Phone number', encoding='UTF-8') in response.data)

    def test_create_account_register_no_email_address(self):
        """Test create account with no email address responds with field required"""

        # creating user
        test_user = {'first_name': 'john',
                     'last_name': 'doe'}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue(bytes('This field is required', encoding='UTF-8') in response.data)

    def test_create_account_register_no_password(self):
        """Test create account with no password returns response field required"""

        # creating user
        test_user = {'first_name': 'john',
                     'last_name': 'doe',
                     'email_address': 'testuser2@email.com',
                     'email_address_confirm': 'wrongemailaddres@email.com', }

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue(bytes('This field is required', encoding='UTF-8') in response.data)

    def test_create_account_register_wrong_email(self):
        """Test create account with mismatching emails returns emails must match"""

        # creating user
        test_user = {'first_name': 'john',
                     'last_name': 'doe',
                     'email_address': 'testuser2@email.com',
                     'email_address_confirm': 'wrongemailaddres@email.com'}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue(bytes('Emails must match', encoding='UTF-8') in response.data)

    def test_create_account_register_wrong_password(self):
        """Test create account with mismatching passwords returns passwords must match"""

        # creating user
        test_user = {'first_name': 'john',
                     'last_name': 'doe',
                     'email_address': 'testuser2@email.com',
                     'email_address_confirm': 'wrongemailaddres@email.com',
                     'password': 'password',
                     'password_confirm': 'wrongpassword'}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue(bytes('Passwords must match', encoding='UTF-8') in response.data)

    def test_create_account_register_no_phone_number(self):
        """Test create account missing phone no. returns field required"""

        # creating user
        test_user = {'first_name': 'john',
                     'last_name': 'doe',
                     'email_address': 'testuser2@email.com',
                     'email_address_confirm': 'wrongemailaddres@email.com',
                     'password': 'password1234',
                     'password_confirm': 'password1234'}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue(bytes('This field is required.', encoding='UTF-8') in response.data)

    def test_create_account_register_illegal_phone_number(self):
        """Test create account with an invalid phone no. returns not a valid UK phone no."""

        # creating user
        test_user = {'first_name': 'john',
                     'last_name': 'doe',
                     'email_address': 'testuser2@email.com',
                     'email_address_confirm': 'wrongemailaddres@email.com',
                     'password': 'password1234',
                     'password_confirm': 'password1234',
                     'phone_number': 'not a number'}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue(bytes('This should be a valid UK number e.g. 01632 496 0018', encoding='UTF-8') in response.data)

    def test_create_account_register_phone_number_too_small(self):
        """Test create account phone no. too small returns length guidance"""

        # creating user
        test_user = {'first_name': 'john',
                     'last_name': 'doe',
                     'email_address': 'testuser2@email.com',
                     'email_address_confirm': 'wrongemailaddres@email.com',
                     'password': 'password1234',
                     'password_confirm': 'password1234',
                     'phone_number': '12345678'}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue(bytes('This should be a valid phone number between 9 and 15 digits', encoding='UTF-8') in response.data)

    def test_create_account_register_phone_number_too_big(self):
        """Test create account phone no. too big returns length guidance"""

        # creating user
        test_user = {'first_name': 'john',
                     'last_name': 'doe',
                     'email_address': 'testuser2@email.com',
                     'email_address_confirm': 'wrongemailaddres@email.com',
                     'password': 'password1234',
                     'password_confirm': 'password1234',
                     'phone_number': '1234567890123456'}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue(bytes('This should be a valid phone number between 9 and 15 digits', encoding='UTF-8') in response.data)

    def test_create_account_register_new_user(self):
        """Test successful create account"""

        # creating user
        test_user = {'first_name': 'john',
                     'last_name': 'doe',
                     'email_address': 'testuser2@email.com',
                     'email_address_confirm': 'testuser2@email.com',
                     'password': 'password',
                     'password_confirm': 'password',
                     'phone_number': '07717275049',
                     'terms_and_conditions': 'Y'}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue(bytes('Enter your account details', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('Your name', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('Email address', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('Create a password', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('Phone number', encoding='UTF-8') in response.data)

    def test_create_duplicate_account(self):
        """Test create a duplicate account returns try a different email this ones in use"""

        # creating user
        test_user = {'first_name': 'john',
                     'last_name': 'doe',
                     'email_address': 'testuser2@email.com',
                     'email_address_confirm': 'testuser2@email.com',
                     'password': 'password',
                     'password_confirm': 'password',
                     'phone_number': '07717275049',
                     'terms_and_conditions': 'Y'}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue(bytes('Enter your account details', encoding='UTF-8') in response.data)

        # Try and create the same user again we should fail this time
        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue(bytes('Please try a different email, this one is in use', encoding='UTF-8') in response.data)

    # def test_surveys_todo_page(self):
    #
    #     # Lets send a post message to the ras_frontstage at the endpoint /sign-in/OAuth.
    #     response = self.app.post('/sign-in/OAuth', data={'username': 'test', 'password': 'test'}, headers=self.headers)
    #
    #     # Our system should still handle this.
    #     self.assertEqual(response.status_code, 200)
    #
    #     response = self.app.get('logged-in', data={'username': 'test', 'password': 'test'}, headers=self.headers)
    #     self.assertTrue(response.status_code, 200)
    #
    #     self.assertTrue(bytes('To do', encoding='UTF-8') in response.data)
    #     self.assertTrue(bytes('History', encoding='UTF-8') in response.data)
    #     self.assertTrue(bytes('Messages', encoding='UTF-8') in response.data)

    # def test_collection_instrument_id(self):
    #     response = self.app.get('/collectioninstrument/id/urn:ons.gov.uk:id:ci:001.001.00001', headers=self.headers)
    #     expected_response = {
    #                             "reference": "rsi-fuel",
    #                             "surveyId": "urn:ons.gov.uk:id:survey:001.001.00001",
    #                             "id": "urn:ons.gov.uk:id:ci:001.001.00001",
    #                             "ciType": "ONLINE",
    #                             "classifiers": {
    #                                 "LEGAL_STATUS": "A",
    #                                 "INDUSTRY": "B"
    #                             }
    #     }
    #     self.assertEqual(expected_response, json.loads(response.data))
