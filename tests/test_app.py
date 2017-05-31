import unittest
from app.application import app, myAdd, logged_in
from app.jwt import encode, decode
from app.config import OAuthConfig
import requests_mock


data_dict_for_jwt_token = {"refresh_token": "eyJhbGciOiJIUzI1NiIsIn",
                                   "access_token": "access_token",
                                   "scope": "[foo,bar,qnx]",
                                   "expires_at": "100123456789",
                                   "username": "johndoe"}

data_dict_zero_length = {"":""}

encoded_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NfdG9rZW4iOiJhY2Nlc3NfdG9rZW4iLCJzY29wZSI6Iltmb28sYmFyLHFueF0iLCJ1c2VybmFtZSI6ImpvaG5kb2UiLCJleHBpcmVzX2F0IjoiMTAwMTIzNDU2Nzg5IiwicmVmcmVzaF90b2tlbiI6ImV5SmhiR2NpT2lKSVV6STFOaUlzSW4ifQ.SIgs3BFhAaJS6s9Q6gm57o9ifVqgAh0AC7-jDigSLZo'


class TestApplication(unittest.TestCase):

    def setUp(self):

        self.app = app.test_client()
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
            }

    # Test we can encode a token with the format shown in data_dict_for_jwt_token
    def test_encode_jwt(self):

        self.assertEquals(encode(data_dict_for_jwt_token), encoded_token)

    # Test we get an error when our token is zero length
    def test_encode_bad_data(self):

        self.assertEquals(encode(data_dict_zero_length),"No data")

    #TODO Test that over a certain size our encode returns the correct error and handles gracefully

    # Test that we can decode our token
    def test_decode_jwt(self):

        self.assertEquals(decode(encoded_token), data_dict_for_jwt_token)

    # By passing a correct token this function should get a HTTP 200
    # data={"error": {"type": "success"}}
    def test_logged_in(self):
        "Testing Logged In"
        response = self.app.get('logged-in', headers=self.headers)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('Error! You are not logged in!' in response.data)

    # By passing an incorrect token this function should get an HTTP 200 with a data dictionary  type set as failed
    # data={"error": {"type": "failed"}}

    # Test we get a user sign in page when we hit this endpoint
    def test_sign_in_page(self):

        response = self.app.get('/sign-in/OAuth', headers=self.headers)

        self.assertEquals(response.status_code, 200)
        self.assertTrue('Sign in', response.data)
        self.assertTrue('Email Address', response.data)
        self.assertTrue('Password', response.data)

    # Test we get an incorrect email or password message when a user who does not exist on the OAuth2 server sign's in
    @requests_mock.mock()                                       # We are using the requests_mock library to fake the
                                                                # call to an OAuth2 server. See: https://requests-mock.readthedocs.io/en/latest/response.html
    def test_sign_in_wrong_details(self, mock_object):

        data = {'refresh_token': '007', 'access_token': '007', 'scope': '[foo,bar]', 'expires_at': 'today', 'username': 'nherriot' }
        url = OAuthConfig.ONS_OAUTH_PROTOCOL + OAuthConfig.ONS_OAUTH_SERVER + OAuthConfig.ONS_TOKEN_ENDPOINT
        #m.post('http://localhost:8000/api/v1/tokens/', status_code=401, text=str(data))

        # Here we place a listener on this URL. This is the URL of the OAuth2 server. We send a 401 to reject the request
        # from the ras_frontstage to get a token for this user. See application.py login_OAuth(). And the call to oauth.fetch_token
        mock_object.post(url, status_code= 401, json={'detail': 'Unauthorized user credentials'})

        # Lets send a post message to the ras_frontstage at the endpoint /sign-in/OAuth.
        response = self.app.post('/sign-in/OAuth', data={'username': 'test', 'password': 'test'}, headers=self.headers)

        self.assertEquals(response.status_code, 200)                        # Our system should still handle this.
        self.assertTrue('Incorrect email or password' in response.data)     # Check this guy has an incorrect email.
        self.assertTrue('Sign in' in response.data)
        self.assertTrue('Email Address' in response.data)
        self.assertTrue('Password' in response.data)


    # Test we have a create account page using a GET request
    def test_create_account_get_page(self):

        response = self.app.get('create-account/enter-account-details/', headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue('Enter your account details' in response.data)
        self.assertTrue('Your name' in response.data)
        self.assertTrue('Email address' in response.data)
        self.assertTrue('Create a password' in response.data)
        self.assertTrue('Phone number' in response.data)

    def test_create_account_register_no_email_address(self):

        # creating user
        test_user = {'first_name':'john',
                'last_name':'doe'}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue('This field is required' in response.data)

    def test_create_account_register_no_password(self):

        # creating user
        test_user = {'first_name':'john',
                'last_name':'doe',
                'email_address':'testuser2@email.com',
                'email_address_confirm':'wrongemailaddres@email.com',}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue('This field is required' in response.data)

    def test_create_account_register_wrong_email(self):

        # creating user
        test_user = {'first_name':'john',
                'last_name':'doe',
                'email_address':'testuser2@email.com',
                'email_address_confirm':'wrongemailaddres@email.com'}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue('Emails must match' in response.data)

    def test_create_account_register_wrong_password(self):

        # creating user
        test_user = {'first_name':'john',
                'last_name':'doe',
                'email_address':'testuser2@email.com',
                'email_address_confirm':'wrongemailaddres@email.com',
                'password':'password',
                'password_confirm':'wrongpassword'}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue('Passwords must match' in response.data)

    def test_create_account_register_no_phone_number(self):

        # creating user
        test_user = {'first_name':'john',
                'last_name':'doe',
                'email_address':'testuser2@email.com',
                'email_address_confirm':'wrongemailaddres@email.com',
                'password':'password1234',
                'password_confirm':'password1234'}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue('This field is required.' in response.data)

    def test_create_account_register_illegal_phone_number(self):

        # creating user
        test_user = {'first_name':'john',
                'last_name':'doe',
                'email_address':'testuser2@email.com',
                'email_address_confirm':'wrongemailaddres@email.com',
                'password':'password1234',
                'password_confirm':'password1234',
                'phone_number':'not a number'}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue('This should be a valid UK number e.g. 01632 496 0018' in response.data)

    def test_create_account_register_phone_number_to_small(self):

        # creating user
        test_user = {'first_name':'john',
                'last_name':'doe',
                'email_address':'testuser2@email.com',
                'email_address_confirm':'wrongemailaddres@email.com',
                'password':'password1234',
                'password_confirm':'password1234',
                'phone_number':'12345678'}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue('This should be a valid phone number between 9 and 15 digits' in response.data)

    def test_create_account_register_phone_number_to_big(self):

        # creating user
        test_user = {'first_name':'john',
                'last_name':'doe',
                'email_address':'testuser2@email.com',
                'email_address_confirm':'wrongemailaddres@email.com',
                'password':'password1234',
                'password_confirm':'password1234',
                'phone_number':'1234567890123456'}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue('This should be a valid phone number between 9 and 15 digits' in response.data)

    def test_create_account_register_new_user(self):

        # creating user
        test_user = {'first_name':'john',
                'last_name':'doe',
                'email_address':'testuser2@email.com',
                'email_address_confirm':'testuser2@email.com',
                'password':'password',
                'password_confirm':'password',
                'phone_number':'07717275049',
                'terms_and_conditions':'Y'}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        #self.assertTrue('Enter your account details' in response.data)
        #self.assertTrue('Your name' in response.data)
        #self.assertTrue('Email address' in response.data)
        #self.assertTrue('Create a password' in response.data)
        #self.assertTrue('Phone number' in response.data)

    def test_create_duplicate_account(self):

        # creating user
        test_user = {'first_name':'john',
                'last_name':'doe',
                'email_address':'testuser2@email.com',
                'email_address_confirm':'testuser2@email.com',
                'password':'password',
                'password_confirm':'password',
                'phone_number':'07717275049',
                'terms_and_conditions':'Y'}

        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue('Enter your account details' in response.data)

        # Try and create the same user again we should fail this time
        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue('Please try a different email, this one is in use' in response.data)



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
    #     self.assertEquals(expected_response, json.loads(response.data))


