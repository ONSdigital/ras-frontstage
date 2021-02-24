import unittest

import requests_mock

from config import TestingConfig
from frontstage import app
from tests.integration.mocked_services import token, url_resend_expired_account_change_verification, \
    url_verify_email, url_banner_api

encoded_valid_email = 'ImV4YW1wbGVAZXhhbXBsZS5jb20i.vMOqeMafWQpuxbUBRyRs29T0vDI'
encoded_invalid_email = 'abcd'

url_resend_password_email_expired_token = f'{TestingConfig.PARTY_URL}/party-api/v1' \
                                          f'/resend-password-email-expired-token/{token}'


class TestAccountEmailChange(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.email_form = {"email_address": "test@email.com"}
        self.auth_response = {}

    @requests_mock.mock()
    def test_expired_account_email_change_verification_token(self, mock_object):
        with app.app_context():
            app.config['ACCOUNT_EMAIL_CHANGE_ENABLED'] = True
            mock_object.put(url_verify_email, status_code=409)
            mock_object.get(url_banner_api, status_code=404)
            response = self.app.get('/my-account/confirm-account-email-change/test_token')

            self.assertEqual(response.status_code, 200)
            self.assertTrue('Your verification link has expired'.encode() in response.data)
            self.assertTrue('This will require a sign in to your account'.encode() in response.data)

    @requests_mock.mock()
    def test_wrong_account_email_change_verification_token(self, mock_object):
        with app.app_context():
            app.config['ACCOUNT_EMAIL_CHANGE_ENABLED'] = True
            mock_object.put(url_verify_email, status_code=404)
            mock_object.get(url_banner_api, status_code=404)
            response = self.app.get('/my-account/confirm-account-email-change/test_token')

            self.assertEqual(response.status_code, 404)

    @requests_mock.mock()
    def test_success_account_email_change_verification_token(self, mock_object):
        with app.app_context():
            app.config['ACCOUNT_EMAIL_CHANGE_ENABLED'] = True
            mock_object.put(url_verify_email, status_code=200)
            mock_object.get(url_banner_api, status_code=404)
            response = self.app.get('/my-account/confirm-account-email-change/test_token')

            self.assertEqual(response.status_code, 200)
            self.assertTrue(
                'Thank you for changing the email address on your account. '
                'You can now sign in using the new details at'.encode() in response.data)

    @requests_mock.mock()
    def test_resend_account_email_change_verification_token(self, mock_object):
        mock_object.get(url_resend_expired_account_change_verification, status_code=200)
        mock_object.get(url_banner_api, status_code=404)
        response = self.app.get('/my-account/resend-account-email-change-expired-token/test_token',
                                follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Your session has expired'.encode() in response.data)
        self.assertTrue('Sign in'.encode() in response.data)
