import json
import unittest
from unittest.mock import MagicMock

from requests.exceptions import ConnectionError
import requests_mock

from frontstage import app
from frontstage.exceptions.exceptions import ApiError, JWTValidationError


url_oauth = app.config['RAS_FRONTSTAGE_API_SERVICE'] + app.config['SIGN_IN_URL']
get_respondent_by_email_url = app.config['PARTY_SERVICE_URL'] + '/party-api/v1/respondents/email'

with open('tests/test_data/respondent/respondent.json') as json_data:
    respondent_data = json.load(json_data)


class TestErrorHandlers(unittest.TestCase):

    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        self.sign_in_form = {
            "username": "testuser@email.com",
            "password": "password"
        }

    def test_not_found_error(self):
        response = self.app.get('/not-a-url', follow_redirects=True)

        self.assertEqual(response.status_code, 404)
        self.assertTrue('not found'.encode() in response.data)

    # Use bad data to raise an uncaught exception
    @requests_mock.mock()
    def test_server_error(self, mock_request):
        mock_request.get(get_respondent_by_email_url, status_code=200, json=respondent_data)
        mock_request.post(url_oauth, status_code=200)

        response = self.app.post('/sign-in/', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_api_error(self, mock_request):
        response_mock = MagicMock()
        mock_request.get(get_respondent_by_email_url, status_code=200, json=respondent_data)
        mock_request.post(url_oauth, exc=ApiError(response_mock))

        response = self.app.post('sign-in', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_connection_error(self, mock_request):
        mock_exception_request = MagicMock()
        mock_request.get(get_respondent_by_email_url, status_code=200, json=respondent_data)
        mock_request.post(url_oauth, exc=ConnectionError(request=mock_exception_request))

        response = self.app.post('sign-in', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_jwt_validation_error(self, mock_request):
        mock_request.get(get_respondent_by_email_url, status_code=200, json=respondent_data)
        mock_request.post(url_oauth, exc=JWTValidationError)

        response = self.app.post('sign-in', data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 403)
        self.assertTrue('Error - Not signed in'.encode() in response.data)
