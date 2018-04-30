import json
import unittest

import requests_mock

from frontstage import app
from tests.app.mocked_services import url_get_party_email, url_oauth_token, party


encoded_jwt_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZWZyZXNoX3Rva2VuIjoiNmY5NjM0ZGEtYTI3ZS00ZDk3LWJhZjktNjN" \
                    "jOGRjY2IyN2M2IiwiYWNjZXNzX3Rva2VuIjoiMjUwMDM4YzUtM2QxOS00OGVkLThlZWMtODFmNTQyMDRjNDE1Iiwic2NvcGU" \
                    "iOlsiIl0sImV4cGlyZXNfYXQiOjE4OTM0NTk2NjEuMCwidXNlcm5hbWUiOiJ0ZXN0dXNlckBlbWFpbC5jb20iLCJyb2xlIjo" \
                    "icmVzcG9uZGVudCIsInBhcnR5X2lkIjoiZGIwMzZmZDctY2UxNy00MGMyLWE4ZmMtOTMyZTdjMjI4Mzk3In0.hh9sFpiPA-O" \
                    "8kugpDi3_GSDnxWh5rz2e5GQuBx7kmLM"


class TestSignIn(unittest.TestCase):
    """Test case for application endpoints and functionality"""

    def setUp(self):
        self.app = app.test_client()
        self.oauth_token = {
            "id": 1,
            "access_token": "8c77e013-d8dc-472c-b4d3-d4fbe21f80e7",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": "",
            "refresh_token": "b7ac07a6-4c28-43bd-a335-00250b490e9f",
            "party_id": "test-id"
        }
        self.expired_oauth_token = {
            "id": 1,
            "access_token": "8c77e013-d8dc-472c-b4d3-d4fbe21f80e7",
            "expires_in": -1,
            "token_type": "Bearer",
            "scope": "",
            "refresh_token": "b7ac07a6-4c28-43bd-a335-00250b490e9f",
            "party_id": "test-id"
        }
        self.sign_in_form = {
            "username": "testuser@email.com",
            "password": "password"
        }
        self.oauth_error = {
            'error': {
                'status_code': 401,
                'data': {
                    'detail': 'Unauthorized user credentials'
                }
            }
        }

    def test_view_sign_in(self):
        response = self.app.get('/sign-in/', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Sign in'.encode() in response.data)
        self.assertTrue('New to this service?'.encode() in response.data)

    def test_view_sign_in_from_redirect(self):
        response = self.app.get('/', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Sign in'.encode() in response.data)
        self.assertTrue('New to this service?'.encode() in response.data)

    def test_view_sign_in_account_activated(self):
        response = self.app.get('/sign-in?account_activated=True', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Sign in'.encode() in response.data)
        self.assertTrue('You\'ve activated your account'.encode() in response.data)

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
    def test_sign_in_success(self, mock_object):
        mock_object.get(url_get_party_email, json=party)
        mock_object.post(url_oauth_token, status_code=200, json=self.oauth_token)

        response = self.app.post('/sign-in/', data=self.sign_in_form)

        self.assertEqual(response.status_code, 302)
        self.assertTrue('/surveys/'.encode() in response.data)

    @requests_mock.mock()
    def test_sign_in_expired(self, mock_object):
        mock_object.post(url_oauth_token, status_code=200, json=self.expired_oauth_token)

        self.app.get('/sign-in/', data=self.sign_in_form)

        response = self.app.get('/surveys/todo',  follow_redirects=True)
        self.assertEqual(response.status_code, 403)
        self.assertIn(b'Error - Not signed in', response.data)

    @requests_mock.mock()
    def test_sign_in_oauth_fail(self, mock_object):
        mock_object.post(url_oauth_token, status_code=500)

        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_sign_in_party_fail(self, mock_object):
        mock_object.get(url_get_party_email, status_code=500)
        mock_object.post(url_oauth_token, status_code=200, json=self.oauth_token)

        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_sign_in_unauthorised_oauth_credentials(self, mock_object):
        mock_object.post(url_oauth_token, status_code=401, json=self.oauth_error)

        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Incorrect email or password'.encode() in response.data)

    @requests_mock.mock()
    def test_sign_in_locked_account(self, mock_object):
        self.oauth_error['error']['data']['detail'] = 'User account locked'
        mock_object.post(url_oauth_token, status_code=401, json=self.oauth_error)

        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Trouble signing in?'.encode() in response.data)

    @requests_mock.mock()
    def test_sign_in_unverified_account(self, mock_object):
        self.oauth_error['error']['data']['detail'] = 'User account not verified'
        mock_object.post(url_oauth_token, status_code=401, json=self.oauth_error)

        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please follow the link in the verification email'.encode() in response.data)

    @requests_mock.mock()
    def test_sign_in_unknown_response(self, mock_object):
        self.oauth_error['error']['data']['detail'] = 'wat'
        mock_object.post(url_oauth_token, status_code=401, json=self.oauth_error)

        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Incorrect email or password'.encode() in response.data)

    def test_logout(self):
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)
        response = self.app.get('/sign-in/logout', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Sign in'.encode() in response.data)
        self.assertTrue('New to this service?'.encode() in response.data)
        self.assertFalse('Sign out'.encode() in response.data)
