import unittest

import requests_mock

from unittest.mock import patch
from frontstage.common import verification
from config import TestingConfig
from frontstage import app
from tests.app.mocked_services import token, url_password_change, url_reset_password_request, \
    url_verify_token, url_get_respondent_by_email

encoded_valid_email = 'ImV4YW1wbGVAZXhhbXBsZS5jb20i.vMOqeMafWQpuxbUBRyRs29T0vDI'
encoded_invalid_email = 'abcd'

url_resend_password_email_expired_token = f'{TestingConfig.PARTY_URL}/party-api/v1' \
                                          f'/resend-password-email-expired-token/{token}'


class TestPasswords(unittest.TestCase):

    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        self.email_form = {"email_address": "test@email.com"}
        self.oauth2_response = {
            'id': 1,
            'access_token': '99a81f9c-e827-448b-8fa7-d563b76137ca',
            'expires_in': 3600,
            'token_type': 'Bearer',
            'scope': '',
            'refresh_token': 'a74fd471-6981-4503-9f59-00d45d339a15'
        }
        self.password_form = {"password": "Gizmo007!", "password_confirm": "Gizmo007!"}

    def test_forgot_password_get(self):
        response = self.app.get("passwords/forgot-password", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('reset your password'.encode() in response.data)

    @requests_mock.mock()
    def test_forgot_password_post_success(self, mock_object):
        mock_object.post(url_reset_password_request, status_code=200)
        mock_object.get(url_get_respondent_by_email, status_code=200, json={"firstName": "Bob", "id": "123456"})

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Check your email'.encode() in response.data)

    def test_forgot_password_post_no_email(self):
        self.email_form['email_address'] = ""

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Invalid email'.encode() in response.data)

    def test_forgot_password_post_invalid_email(self):
        self.email_form['email_address'] = "aaaaa"

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Invalid email'.encode() in response.data)

    @requests_mock.mock()
    def test_forgot_password_post_unrecognised_email_party(self, mock_object):
        mock_object.post(url_reset_password_request, status_code=404)
        mock_object.get(url_get_respondent_by_email, status_code=200, json={"firstName": "Bob", "id": "123456"})

        self.email_form['email_address'] = "test@email.com"

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Check your email'.encode() in response.data)

    @requests_mock.mock()
    def test_forgot_password_post_api_call_fail(self, mock_object):
        mock_object.post(url_reset_password_request, status_code=500)

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('An error has occurred'.encode() in response.data)

    def test_check_valid_email_token(self):
        response = self.app.get(f"passwords/forgot-password/check-email?email={encoded_valid_email}",
                                follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Check your email'.encode() in response.data)

    def test_check_invalid_email_token(self):
        response = self.app.get(f"passwords/forgot-password/check-email?email={encoded_invalid_email}",
                                follow_redirects=True)

        self.assertEqual(response.status_code, 404)
        self.assertTrue("Page not found".encode() in response.data)

    def test_check_no_email_token(self):
        response = self.app.get("passwords/forgot-password/check-email", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('reset your password'.encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_get_success(self, mock_object):
        mock_object.get(url_verify_token, status_code=200)
        with app.app_context():
            token = verification.generate_email_token("test.com")
        response = self.app.get(f"passwords/reset-password/{token}", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Reset your password'.encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_get_expired_token(self, mock_object):
        mock_object.get(url_verify_token, status_code=409)

        response = self.app.get(f"passwords/reset-password/{token}", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Your link has expired'.encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_get_invalid_token(self, mock_object):
        mock_object.get(url_verify_token, status_code=500)

        response = self.app.get(f"passwords/reset-password/{token}", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Your link has expired'.encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_get_party_fail(self, mock_object):
        mock_object.get(url_verify_token, status_code=500)

        response = self.app.get(f"passwords/reset-password/{token}", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Your link has expired'.encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_post_success(self, mock_object):
        mock_object.put(url_password_change, status_code=200)
        password_form = {"password": "Gizmo007!", "password_confirm": "Gizmo007!"}
        with app.app_context():
            token = verification.generate_email_token("test.com")
        response = self.app.post(f"passwords/reset-password/{token}", data=password_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Your password has been changed'.encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_post_token_expired(self, mock_object):
        mock_object.put(url_password_change, status_code=409)
        password_form = {"password": "Gizmo007!", "password_confirm": "Gizmo007!"}
        with app.app_context():
            token = verification.generate_email_token("test.com")
        response = self.app.post(f"passwords/reset-password/{token}", data=password_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Your link has expired'.encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_post_token_invalid(self, mock_object):
        mock_object.put(url_password_change, status_code=404)
        password_form = {"password": "Gizmo007!", "password_confirm": "Gizmo007!"}
        with app.app_context():
            token = verification.generate_email_token("test.com")
        response = self.app.post(f"passwords/reset-password/{token}", data=password_form, follow_redirects=True)

        self.assertEqual(response.status_code, 404)
        self.assertTrue('Page not found'.encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_post_different_passwords(self, mock_object):
        mock_object.get(url_verify_token, status_code=200)
        password_form = {"password": "Gizmo008!", "password_confirm": "Gizmo007!"}
        with app.app_context():
            token = verification.generate_email_token("test.com")
        response = self.app.post(f"passwords/reset-password/{token}", data=password_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Your passwords do not match'.encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_post_requirements_fail(self, mock_object):
        mock_object.get(url_verify_token, status_code=200)
        password_form = {"password": "Gizmo007a", "password_confirm": "Gizmo007a"}
        with app.app_context():
            token = verification.generate_email_token("test.com")
        response = self.app.post(f"passwords/reset-password/{token}", data=password_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        print(response.data)
        self.assertTrue("Your password doesn&#39;t meet the requirements".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_no_password(self, mock_object):
        mock_object.get(url_verify_token, status_code=200)
        password_form = {}
        with app.app_context():
            token = verification.generate_email_token("test.com")
        response = self.app.post(f"passwords/reset-password/{token}", data=password_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Password is required".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_put_party_service_fail(self, mock_object):
        mock_object.put(url_password_change, status_code=500)
        password_form = {"password": "Gizmo007!", "password_confirm": "Gizmo007!"}
        with app.app_context():
            token = verification.generate_email_token("test.com")

        response = self.app.post(f"passwords/reset-password/{token}", data=password_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue("An error has occurred".encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.notify_controller.NotifyGateway.request_to_notify")
    def test_resend_verification_email_using_expired_token(self, mock_object, mock_notify):
        mock_object.get('http://localhost:8081/party-api/v1/respondents/email', status_code=200,
                        json={"firstName": "Bob", "id": "123456"})
        with app.app_context():
            token = verification.generate_email_token("test@test.com")
        response = self.app.get(f'passwords/resend-password-email-expired-token/{token}',
                                follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        mock_notify.assert_called_once()
        self.assertTrue('Check your email'.encode() in response.data)

    @requests_mock.mock()
    def test_fail_resend_verification_email_using_expired_token(self, mock_object):
        mock_object.post(url_resend_password_email_expired_token, status_code=500)
        response = self.app.get(f'passwords/resend-password-email-expired-token/{token}',
                                follow_redirects=True)
        self.assertEqual(response.status_code, 500)
        self.assertTrue('An error has occurred'.encode() in response.data)
