import json
import unittest

import requests_mock

from frontstage import app


with open('tests/test_data/my_party.json') as json_data:
    my_party_data = json.load(json_data)
oauth_token = {
    "id": 503,
    "access_token": "8c77e013-d8dc-472c-b4d3-d4fbe21f80e7",
    "expires_in": 3600,
    "token_type": "Bearer",
    "scope": "",
    "refresh_token": "b7ac07a6-4c28-43bd-a335-00250b490e9f"
}
sign_in_form = {
    "username": "testuser@email.com",
    "password": "password"
}
encoded_jwt_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZWZyZXNoX3Rva2VuIjoiNmY5NjM0ZGEtYTI3ZS00ZDk3LWJhZjktNjN" \
                    "jOGRjY2IyN2M2IiwiYWNjZXNzX3Rva2VuIjoiMjUwMDM4YzUtM2QxOS00OGVkLThlZWMtODFmNTQyMDRjNDE1Iiwic2NvcGU" \
                    "iOlsiIl0sImV4cGlyZXNfYXQiOjE4OTM0NTk2NjEuMCwidXNlcm5hbWUiOiJ0ZXN0dXNlckBlbWFpbC5jb20iLCJyb2xlIjo" \
                    "icmVzcG9uZGVudCIsInBhcnR5X2lkIjoiZGIwMzZmZDctY2UxNy00MGMyLWE4ZmMtOTMyZTdjMjI4Mzk3In0.hh9sFpiPA-O" \
                    "8kugpDi3_GSDnxWh5rz2e5GQuBx7kmLM"

url_party_by_email = app.config['RAS_PARTY_GET_BY_EMAIL'].format(app.config['RAS_PARTY_SERVICE'], "testuser@email.com")
url_oauth_token = app.config['ONS_OAUTH_PROTOCOL'] + app.config['ONS_OAUTH_SERVER'] + app.config['ONS_TOKEN_ENDPOINT']


class TestSignIn(unittest.TestCase):
    """Test case for application endpoints and functionality"""

    def setUp(self):
        self.app = app.test_client()
        self.sign_in_form = sign_in_form

    def test_view_sign_in(self):
        response = self.app.get('/sign-in/', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Sign in'.encode() in response.data)
        self.assertTrue('Have an enrolment code?'.encode() in response.data)

    def test_view_sign_in_account_activated(self):
        response = self.app.get('/sign-in?account_activated=True', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Sign in'.encode() in response.data)
        self.assertTrue('You\'ve activated your account'.encode() in response.data)

    @requests_mock.mock()
    def test_sign_in(self, mock_object):
        mock_object.post(url_oauth_token, status_code=201, json=oauth_token)
        mock_object.get(url_party_by_email, status_code=200, json=my_party_data)

        response = self.app.post('/sign-in/', data=self.sign_in_form)

        self.assertEqual(response.status_code, 302)
        self.assertTrue('/surveys/'.encode() in response.data)

    @requests_mock.mock()
    def test_sign_in_unauthorised_oauth_credentials(self, mock_object):
        self.sign_in_form['username'] = 'testuser@email.com'
        self.sign_in_form['password'] = 'password'
        mock_object.post(url_oauth_token, status_code=401, json={"detail": "Unauthorized user credentials"})

        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Incorrect email or password'.encode() in response.data)

    @requests_mock.mock()
    def test_sign_in_locked_account(self, mock_object):
        self.sign_in_form['username'] = 'testuser@email.com'
        self.sign_in_form['password'] = 'password'
        mock_object.post(url_oauth_token, status_code=401, json={"detail": "User account locked"})

        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Trouble signing in?'.encode() in response.data)

    @requests_mock.mock()
    def test_sign_in_unverified_account(self, mock_object):
        self.sign_in_form['username'] = 'testuser@email.com'
        self.sign_in_form['password'] = 'password'
        mock_object.post(url_oauth_token, status_code=401, json={"detail": "User account not verified"})

        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please follow the link in the verification email'.encode() in response.data)

    @requests_mock.mock()
    def test_sign_in_unknown_response(self, mock_object):
        self.sign_in_form['username'] = 'testuser@email.com'
        self.sign_in_form['password'] = 'password'
        mock_object.post(url_oauth_token, status_code=401, json={"detail": "wat"})

        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Incorrect email or password'.encode() in response.data)

    @requests_mock.mock()
    def test_sign_in_oauth_fail(self, mock_object):
        self.sign_in_form['username'] = 'testuser@email.com'
        self.sign_in_form['password'] = 'password'
        mock_object.post(url_oauth_token, status_code=500)

        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    def test_sign_in_no_username(self):
        del self.sign_in_form['username']

        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Email Address is required'.encode() in response.data)

    def test_sign_in_invalid_username(self):
        self.sign_in_form['username'] = 'aaa'

        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Your email should be of the form'.encode() in response.data)

    def test_sign_in_no_password(self):
        self.sign_in_form['username'] = 'testuser@email.com'
        del self.sign_in_form['password']

        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Password is required'.encode() in response.data)

    @requests_mock.mock()
    def test_sign_in_unrecognised_user_party(self, mock_object):
        mock_object.post(url_oauth_token, status_code=201, json=oauth_token)
        mock_object.get(url_party_by_email, status_code=404, json=my_party_data)

        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Incorrect email or password'.encode() in response.data)

    @requests_mock.mock()
    def test_sign_in_party_fail(self, mock_object):
        mock_object.post(url_oauth_token, status_code=201, json=oauth_token)
        mock_object.get(url_party_by_email, status_code=500, json=my_party_data)

        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    def test_logout(self):
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)
        response = self.app.get('/sign-in/logout', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Sign in'.encode() in response.data)
        self.assertTrue('Have an enrolment code?'.encode() in response.data)
        self.assertFalse('Sign out'.encode() in response.data)
