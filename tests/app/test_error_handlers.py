import unittest
from unittest.mock import MagicMock

import requests_mock
from requests.exceptions import ConnectionError

from frontstage import app
from frontstage.exceptions.exceptions import ApiError, JWTValidationError
from tests.app.mocked_services import url_get_respondent_email, url_oauth_token, party


class TestErrorHandlers(unittest.TestCase):

    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        self.sign_in_form = {
            "username": "testuser@email.com",
            "password": "password"
        }
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"# NOQA
        }

    def test_not_found_error(self):
        response = self.app.get('/not-a-url', follow_redirects=True)

        self.assertEqual(response.status_code, 404)
        self.assertTrue('not found'.encode() in response.data)

    # Use bad data to raise an uncaught exception
    @requests_mock.mock()
    def test_server_error(self, mock_request):
        mock_request.post(url_oauth_token, status_code=200)

        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_api_error(self, mock_request):
        response_mock = MagicMock()
        logger_mock = MagicMock()
        mock_request.post(url_oauth_token, exc=ApiError(logger_mock, response_mock))

        response = self.app.post('sign-in', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_connection_error(self, mock_request):
        mock_exception_request = MagicMock()
        mock_request.post(url_oauth_token, exc=ConnectionError(request=mock_exception_request))

        response = self.app.post('sign-in', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_jwt_validation_error(self, mock_request):
        mock_request.get(url_get_respondent_email, json=party)
        mock_request.post(url_oauth_token, exc=JWTValidationError)

        response = self.app.post('sign-in', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 403)
        self.assertTrue('Error - Not signed in'.encode() in response.data)

    def test_csrf_token_expired(self):
        app.config['WTF_CSRF_ENABLED'] = True
        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)
        self.assertEqual(response.status_code, 400)
        app.config['WTF_CSRF_ENABLED'] = False

    def test_csrf_token_expired_on_sending_message(self):
        app.config['WTF_CSRF_ENABLED'] = True
        self.app.set_cookie('localhost', 'authorization', 'session_key')
        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data='{"test":"test"}', headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('To help protect your information we have signed you out.'.encode() in response.data)
        app.config['WTF_CSRF_ENABLED'] = False
