import unittest
from app.application import app
from app.jwt import encode, decode
from app.config import OAuthConfig, Config
import json
import requests_mock

with open('tests/my-surveys.json') as json_data:
    my_surveys = json.load(json_data)



print("my repository values are:{}".format(my_surveys['rows'][0]['businessData']['businessRef']))

returned_token = {"id":6,"access_token":"a712f0f9-d00d-447a-b143-49984ca3db68","expires_in":3600,"token_type":"Bearer","scope":"","refresh_token":"37ca04d2-6b6c-4854-8e85-f59c2cc7d3de"}
data_dict_for_jwt_token={'refresh_token': 'e6bde0f6-e123-4dcf-9567-74f4d072fc71', 'access_token': 'f418d491-eeda-47cb-b3e3-0d5d7b97ee6d', 'username': 'johndoe', 'expires_at': '100123456789', 'scope': '[foo,bar,qnx]'}

party_id = "3b136c4b-7a14-4904-9e01-13364dd7b972"

data_dict_for_jwt_token2 = {
 "refresh_token": "e6bde0f6-e123-4dcf-9567-74f4d072fc71",
 "access_token": "f418d491-eeda-47cb-b3e3-0d5d7b97ee6d",
 "username": "johndoe",
 "expires_at": "100123456789",
 "scope": "[foo,bar,qnx]"
}

test_user = {'first_name': 'john',
             'last_name': 'doe',
             'email_address': 'testuser2@email.com',
             'email_address_confirm': 'testuser2@email.com',
             'password': 'password',
             'password_confirm': 'password',
             'phone_number': '07717275049',
             'terms_and_conditions': 'Y'}



data_dict_zero_length = {"": ""}

encoded_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyZWZyZXNoX3Rva2VuIjoiZTZiZGUwZjYtZTEyMy00ZGNmLTk1NjctNzRmNGQwNzJmYzcxIiwiYWNjZXNzX3Rva2VuIjoiZjQxOGQ0OTEtZWVkYS00N2NiLWIzZTMtMGQ1ZDdiOTdlZTZkIiwidXNlcm5hbWUiOiJqb2huZG9lIiwic2NvcGUiOiJbZm9vLGJhcixxbnhdIiwiZXhwaXJlc19hdCI6IjEwMDEyMzQ1Njc4OSJ9.NhOb7MK_SaaW8wvqwbiiAv5N-oaN8SHYli2Z-NpkJ2A'

class TestApplication(unittest.TestCase):
    """Test case for application endpoints and functionality"""

    def setUp(self):

        self.app = app.test_client()
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
            }

    # Test we can encode a token with the format shown in data_dict_for_jwt_token
    def test_encode_jwt(self):

        # first encode our dictionary object
        myEncoded_dictionary = encode(data_dict_for_jwt_token)

        # now decode and ensure we have the same thing.
        myDecoded_dictionary = decode(myEncoded_dictionary)

        # now compare that values are the same in the dictionary
        self.assertEqual(myDecoded_dictionary, data_dict_for_jwt_token)

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
        response = self.app.get('/', headers=self.headers)

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

        # Here we place a listener on this URL. This is the URL of the OAuth2 server. We send a 401 to reject the request
        # from the ras_frontstage to get a token for this user. See application.py login(). And the call to oauth.fetch_token
        mock_object.post(url, status_code=401, json={'detail': 'Unauthorized user credentials'})

        # Lets send a post message to the ras_frontstage at the endpoint /sign-in.
        response = self.app.post('/sign-in', data={'username': 'test', 'password': 'test'}, headers=self.headers)

        # Our system should still handle this.
        self.assertEqual(response.status_code, 200)

        # Check this guy has an incorrect email.
        self.assertTrue(bytes('Incorrect email or password', encoding='UTF-8') in response.data)


    # Test we get survey data once a user signs in properly. This means we have to mock up OAuth2 server sending a
    # Token. The ras_frontstage will then send a request for data to the API Gateway / Party Service, we Mock this too
    # and reply with survey data. See: https://requests-mock.readthedocs.io/en/latest/response.html
    @requests_mock.mock()
    def test_sign_in_view_survey_data(self, mock_object):
        """Test we display survey data after signing in correctly
        """

        # Build URL's which is used to talk to the OAuth2 server
        #url_sign_in_user = OAuthConfig.ONS_OAUTH_PROTOCOL + OAuthConfig.ONS_OAUTH_SERVER + OAuthConfig.ONS_ADMIN_ENDPOINT
        url_get_token = OAuthConfig.ONS_OAUTH_PROTOCOL + OAuthConfig.ONS_OAUTH_SERVER + OAuthConfig.ONS_TOKEN_ENDPOINT
        url_get_survey_data = Config.API_GATEWAY_SURVEYS_URL + 'todo/' + party_id

        # Here we place a listener on the URL's The flow of events are:
        # 1) The ras_frontstage signs in OAuth2 user.
        # 2) The OAuth2 replies with a HTTP 200 OK and token data.
        # 3) The ras_frontstage requests to view survey data from the Part Service.
        # 4) The Part Service replys with survey data.
        # 5) The ras_frontstage displays surve data.
        #
        # This means we need to mock 2) and 4)
        #
        # Here we place a listener on our URLs. This is the URL of the OAuth2 server and Party Server

        mock_object.post(url_get_token, status_code=200, json=returned_token)
        mock_object.get(url_get_survey_data, status_code=200, json=my_surveys)

        # 1) Send a POST message to sign in as a test user
        #   User                        FS                      OAuth2                  PS
        #   ----                        --                      ------                  --
        #           Sign-in             |
        #   --------------------------->|
        response = self.app.post('/sign-in', data={'username': 'testuser@email.com', 'password': 'password'}, headers=self.headers)

        # 2) Mock object gets returned from our simulated OAuth2 server
        #   User                        FS                      OAuth2                  PS
        #   ----                        --                      ------                  --
        #                               |       get-token
        #                               |------------------------->|
        #                               |<-------------------------|

        print ("The response data is: {}".format(response.data))
        # Our system should check the response data.
        self.assertEqual(response.status_code, 302)
        self.assertTrue(bytes('You should be redirected automatically to target URL', encoding='UTF-8') in response.data)

        # 3) ras_frontstage sends a redirect to /. So we simulate our redirect and call the / page
        #   User                        FS                      OAuth2                  PS
        #   ----                        --                      ------                  --
        #           redirect            |
        #   <---------------------------|
        #           /           |
        #   --------------------------->|
        response = self.app.post('/', data={}, headers=self.headers)

        # 4) Mock object gets returned from our simulated gateway to provide survey data.
        #   User                        FS                      OAuth2                  PS
        #   ----                        --                      ------                  --
        #                               |                 request survey data           |
        #                               |---------------------------------------------->|
        #                               |                 mock survey data              |
        #                               |<----------------------------------------------|

        # 5) Check our response has survey data. In particular lets check we can see the RUREF value.
        #   User                        FS                      OAuth2                  PS
        #   ----                        --                      ------                  --
        #   |                           |                                               |
        #   |     / response    |                                               |
        #   |<------------------------- |                                               |
        print ("The response data is: {}".format(response.data))
        print("my repository values are:{}".format(my_surveys['rows'][0]['businessData']['businessRef']))

        self.assertTrue(bytes(my_surveys['rows'][0]['businessData']['businessRef'], encoding='UTF-8') in response.data)


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

    @requests_mock.mock()
    def test_create_account_register_new_user(self, mock_object):
        """Test successful create account"""

        # Build URL's which is used to talk to the OAuth2 server
        url_create_user = OAuthConfig.ONS_OAUTH_PROTOCOL + OAuthConfig.ONS_OAUTH_SERVER + OAuthConfig.ONS_ADMIN_ENDPOINT
        url_get_token = OAuthConfig.ONS_OAUTH_PROTOCOL + OAuthConfig.ONS_OAUTH_SERVER + OAuthConfig.ONS_TOKEN_ENDPOINT
        url_get_survey_data = Config.API_GATEWAY_PARTY_URL + 'respondents'

        # Here we place a listener on the URL's The flow of events are:
        # 1) The ras_frontstage creates a user on the OAuth2 server.
        # 2) The OAuth2 replies with a HTTP 200 OK.
        # 3) The ras_frontstage requests a client Token from the OAuth2 to allow it to speak with the PartyServer.
        # 4) The OAuth2 sends a token, refresh token, TTL and scopes.
        # 5) The ras_frontstage requests survey data from the Party Service.
        # 6) The Party Servie replys with survey data.
        # This means we need to mock 2) 4) and  6)
        #
        mock_object.post(url_create_user, status_code=200, json={"account": "testuser2@email.com", "created":"success"})
        mock_object.post(url_get_token, status_code=200, json=returned_token)
        mock_object.post(url_get_survey_data, status_code=200, json=my_surveys)


        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        print ("response object is: {}".format(response.data))
        self.assertTrue(response.status_code, 301)
        self.assertTrue(bytes('Please follow the link in the email to confirm your email address and finish setting up your account.', encoding='UTF-8') in response.data)


    # Test we present the user with a page to say this email is already in use when we register the same user twice.
    # We are using the requests_mock library to fake the call to an OAuth2 server and the party service.
    # See: https://requests-mock.readthedocs.io/en/latest/response.html
    @requests_mock.mock()
    def test_create_duplicate_account(self, mock_object):
        """Test create a duplicate account returns 'try a different email this ones in use' """

        # Build URL's which is used to talk to the OAuth2 server
        url_create_user = OAuthConfig.ONS_OAUTH_PROTOCOL + OAuthConfig.ONS_OAUTH_SERVER + OAuthConfig.ONS_ADMIN_ENDPOINT

        # Here we place a listener on this URL. This is the URL of the OAuth2 server. We send a 401 to reject the request
        # from the ras_frontstage to get a token for this user. See application.py login()

        mock_object.post(url_create_user, status_code=401, json= {"detail":"Duplicate user credentials"})


        response = self.app.post('create-account/enter-account-details/', data=test_user, headers=self.headers)

        self.assertTrue(response.status_code, 200)
        self.assertTrue(bytes('Please try a different email, this one is in use', encoding='UTF-8') in response.data)


    # def test_surveys_todo_page(self):
    #
    #     # Lets send a post message to the ras_frontstage at the endpoint /sign-in.
    #     response = self.app.post('/sign-in', data={'username': 'test', 'password': 'test'}, headers=self.headers)
    #
    #     # Our system should still handle this.
    #     self.assertEqual(response.status_code, 200)
    #
    #     response = self.app.get('/', data={'username': 'test', 'password': 'test'}, headers=self.headers)
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
