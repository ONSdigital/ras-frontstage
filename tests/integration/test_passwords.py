import unittest
from unittest.mock import patch

import requests_mock

from config import TestingConfig
from frontstage import app
from frontstage.common import verification
from tests.integration.mocked_services import (
    token,
    url_banner_api,
    url_get_respondent_by_email,
    url_password_change,
    url_reset_password_request,
    url_verify_token,
)

encoded_valid_email = "ImV4YW1wbGVAZXhhbXBsZS5jb20i.vMOqeMafWQpuxbUBRyRs29T0vDI"
encoded_invalid_email = "abcd"

url_resend_password_email_expired_token = (
    f"{TestingConfig.PARTY_URL}/party-api/v1" f"/resend-password-email-expired-token/{token}"
)
url_password_reset_counter = f"{app.config['PARTY_URL']}/party-api/v1/respondents/123456/password-reset-counter"


class TestPasswords(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        self.email_form = {"email_address": "test@email.com"}
        self.auth_response = {}
        self.password_form = {"password": "Gizmo007!", "password_confirm": "Gizmo007!"}

    @requests_mock.mock()
    def test_forgot_password_get(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get("passwords/forgot-password", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("reset your password".encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.notify_controller.NotifyGateway.request_to_notify")
    def test_forgot_password_post_success(self, mock_request, mock_notify):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_reset_password_request, status_code=200)
        mock_request.get(url_get_respondent_by_email, status_code=200, json={"firstName": "Bob", "id": "123456"})
        mock_request.get(url_password_reset_counter, status_code=200, json={"counter": 0})
        mock_request.delete(url_password_reset_counter, status_code=200, json={})
        mock_request.post(
            f"{TestingConfig.PARTY_URL}/party-api/v1/respondents/123456/password-verification-token",
            status_code=200,
            json={"message": "Successfully added token"},
        )

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        mock_notify.assert_called_once()
        self.assertTrue("Check your email".encode() in response.data)

    @requests_mock.mock()
    def test_forgot_password_post_no_email(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        self.email_form["email_address"] = ""

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("There is 1 error on this page".encode() in response.data)

    @requests_mock.mock()
    def test_forgot_password_post_invalid_email(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        self.email_form["email_address"] = "aaaaa"

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Invalid email".encode() in response.data)

    @requests_mock.mock()
    def test_forgot_password_post_unrecognised_email_party(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_reset_password_request, status_code=404)
        mock_request.get(url_get_respondent_by_email, status_code=404)

        self.email_form["email_address"] = "test@email.com"

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Something went wrong".encode() in response.data)

    @requests_mock.mock()
    def test_forgot_password_post_api_call_fail(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_reset_password_request, status_code=500)

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue("An error has occurred".encode() in response.data)

    @requests_mock.mock()
    def test_check_valid_email_token(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get(
            f"passwords/forgot-password/check-email?email={encoded_valid_email}", follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Check your email".encode() in response.data)

    @requests_mock.mock()
    def test_check_invalid_email_token(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get(
            f"passwords/forgot-password/check-email?email={encoded_invalid_email}", follow_redirects=True
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue("Page not found".encode() in response.data)

    @requests_mock.mock()
    def test_check_no_email_token(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get("passwords/forgot-password/check-email", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("reset your password".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_get_success(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_verify_token, status_code=200)
        with app.app_context():
            token = verification.generate_email_token("test.com")
        mock_request.get(
            url_get_respondent_by_email,
            status_code=200,
            json={"firstName": "Bob", "id": "123456", "password_verification_token": token},
        )
        response = self.app.get(f"passwords/reset-password/{token}", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Reset your password".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_get_expired_token(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_verify_token, status_code=409)

        response = self.app.get(f"passwords/reset-password/{token}", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Your link has expired".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_get_invalid_token(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_verify_token, status_code=500)

        response = self.app.get(f"passwords/reset-password/{token}", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Your link has expired".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_get_party_fail(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_verify_token, status_code=500)

        response = self.app.get(f"passwords/reset-password/{token}", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Your link has expired".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_get_token_not_found(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_verify_token, status_code=200)
        with app.app_context():
            token = verification.generate_email_token("failing_email_token.com")
        mock_request.get(
            url_get_respondent_by_email,
            status_code=200,
            json={"firstName": "Bob", "id": "123456", "password_verification_token": []},
        )
        response = self.app.get(f"passwords/reset-password/{token}", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Your link is invalid or has already been used".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_post_success(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.put(url_password_change, status_code=200)
        password_form = {"password": "Gizmo007!Gizmo", "password_confirm": "Gizmo007!Gizmo"}
        with app.app_context():
            token = verification.generate_email_token("test.com")
        mock_request.get(
            url_get_respondent_by_email,
            status_code=200,
            json={"firstName": "Bob", "id": "123456", "password_verification_token": token},
        )
        mock_request.delete(
            f"{TestingConfig.PARTY_URL}/party-api/v1/respondents/123456/password-verification-token/{token}",
            status_code=200,
            json={"message": "Successfully removed token"},
        )
        mock_request.delete(url_password_reset_counter, status_code=200)
        response = self.app.post(f"passwords/reset-password/{token}", data=password_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Your password has been changed".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_respondent_not_found(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(
            url_get_respondent_by_email,
            status_code=404,
            json={},
        )

        with app.app_context():
            token = verification.generate_email_token("failing_email_token.com")

        response = self.app.get(f"passwords/reset-password/{token}", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Your link is invalid or has already been used".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_post_token_expired(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.put(url_password_change, status_code=409)
        password_form = {"password": "Gizmo007!Gizmo", "password_confirm": "Gizmo007!Gizmo"}
        with app.app_context():
            token = verification.generate_email_token("test.com")
        response = self.app.post(f"passwords/reset-password/{token}", data=password_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Your link has expired".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_post_token_invalid(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.put(url_password_change, status_code=404)
        password_form = {"password": "Gizmo007!Gizmo", "password_confirm": "Gizmo007!Gizmo"}
        with app.app_context():
            token = verification.generate_email_token("test.com")
        response = self.app.post(f"passwords/reset-password/{token}", data=password_form, follow_redirects=True)

        self.assertEqual(response.status_code, 404)
        self.assertTrue("Page not found".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_post_different_passwords(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_verify_token, status_code=200)
        password_form = {"password": "Gizmo008!", "password_confirm": "Gizmo007!"}
        with app.app_context():
            token = verification.generate_email_token("test.com")
        mock_request.get(
            url_get_respondent_by_email,
            status_code=200,
            json={"firstName": "Bob", "id": "123456", "password_verification_token": token},
        )
        response = self.app.post(f"passwords/reset-password/{token}", data=password_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Your passwords do not match".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_post_requirements_fail(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_verify_token, status_code=200)
        password_form = {"password": "Gizmo007a", "password_confirm": "Gizmo007a"}
        with app.app_context():
            token = verification.generate_email_token("test.com")
        mock_request.get(
            url_get_respondent_by_email,
            status_code=200,
            json={"firstName": "Bob", "id": "123456", "password_verification_token": token},
        )
        response = self.app.post(f"passwords/reset-password/{token}", data=password_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Your password doesn't meet the requirements".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_no_password(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_verify_token, status_code=200)
        password_form = {}
        with app.app_context():
            token = verification.generate_email_token("test.com")
        mock_request.get(
            url_get_respondent_by_email,
            status_code=200,
            json={"firstName": "Bob", "id": "123456", "password_verification_token": token},
        )
        response = self.app.post(f"passwords/reset-password/{token}", data=password_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Password is required".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_put_party_service_fail(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.put(url_password_change, status_code=500)
        password_form = {"password": "Gizmo007!Gizmo", "password_confirm": "Gizmo007!Gizmo"}
        with app.app_context():
            token = verification.generate_email_token("test.com")

        response = self.app.post(f"passwords/reset-password/{token}", data=password_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue("An error has occurred".encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.notify_controller.NotifyGateway.request_to_notify")
    def test_resend_verification_email_using_expired_token(self, mock_request, mock_notify):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(
            "http://localhost:8081/party-api/v1/respondents/email",
            status_code=200,
            json={"firstName": "Bob", "id": "123456"},
        )
        with app.app_context():
            token = verification.generate_email_token("test@test.com")
        mock_request.get(url_password_reset_counter, status_code=200, json={"counter": 0})
        mock_request.delete(url_password_reset_counter, status_code=200, json={})
        mock_request.post(
            f"{TestingConfig.PARTY_URL}/party-api/v1/respondents/123456/password-verification-token",
            status_code=200,
            json={"message": "Successfully added token"},
        )
        response = self.app.get(f"passwords/resend-password-email-expired-token/{token}", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        mock_notify.assert_called_once()
        self.assertTrue("Check your email".encode() in response.data)

    @requests_mock.mock()
    def test_fail_resend_verification_email_using_expired_token(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_resend_password_email_expired_token, status_code=500)
        response = self.app.get(f"passwords/resend-password-email-expired-token/{token}", follow_redirects=True)
        self.assertEqual(response.status_code, 500)
        self.assertTrue("An error has occurred".encode() in response.data)

    @requests_mock.mock()
    def test_too_many_reset_attempts(self, mock_request):
        with app.app_context():
            token = verification.generate_email_token("test.com")
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_reset_password_request, status_code=200)
        mock_request.get(
            url_get_respondent_by_email,
            status_code=200,
            json={"firstName": "Bob", "id": "123456", "password_verification_token": token},
        )
        mock_request.get(url_password_reset_counter, status_code=200, json={"counter": 5})
        mock_request.delete(url_password_reset_counter, status_code=200, json={})
        mock_request.post(
            f"{TestingConfig.PARTY_URL}/party-api/v1/respondents/123456/password-verification-token",
            status_code=200,
            json={"message": "Successfully added token"},
        )

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "You've tried to reset your password too many times".encode(),
            response.data,
        )

    @requests_mock.mock()
    @patch("frontstage.controllers.notify_controller.NotifyGateway.request_to_notify")
    def test_reset_password_reset_counter(self, mock_request, mock_notify):
        token = "InRlc3RAZW1haWwuY29tIg.YlARnw.8hj0e_lcI_Wq5y0iHYbvDxHnio0"
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_reset_password_request, status_code=200)
        mock_request.get(
            url_get_respondent_by_email,
            status_code=200,
            json={"firstName": "Bob", "id": "123456", "password_verification_token": token},
        )
        mock_request.get(url_password_reset_counter, status_code=200, json={"counter": 5})
        mock_request.delete(url_password_reset_counter, status_code=200, json={"message": "Successfully reset counter"})
        mock_request.put(
            url_password_reset_counter, status_code=200, json={"message": "Successfully increased counter"}
        )
        mock_request.post(
            f"{TestingConfig.PARTY_URL}/party-api/v1/respondents/123456/password-verification-token",
            status_code=200,
            json={"message": "Successfully added token"},
        )

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Check your email".encode(), response.data)
        mock_notify.assert_called_once()

    @requests_mock.mock()
    def test_reset_password_reset_counter_party_fail(self, mock_request):
        token = "InRlc3RAZW1haWwuY29tIg.YlARnw.8hj0e_lcI_Wq5y0iHYbvDxHnio0"
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_reset_password_request, status_code=200)
        mock_request.get(
            url_get_respondent_by_email,
            status_code=200,
            json={"firstName": "Bob", "id": "123456", "password_verification_token": token},
        )
        mock_request.get(url_password_reset_counter, status_code=200, json={"counter": 5})
        mock_request.delete(url_password_reset_counter, status_code=409)
        mock_request.post(
            f"{TestingConfig.PARTY_URL}/party-api/v1/respondents/123456/password-verification-token",
            status_code=200,
            json={"message": "Successfully added token"},
        )

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Something went wrong".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.notify_controller.NotifyGateway.request_to_notify")
    def test_resend_verification_email_using_expired_token_when_counter_is_greater_than_0(
        self, mock_request, mock_notify
    ):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(
            "http://localhost:8081/party-api/v1/respondents/email",
            status_code=200,
            json={"firstName": "Bob", "id": "123456"},
        )
        with app.app_context():
            token = verification.generate_email_token("test@test.com")
        mock_request.get(url_password_reset_counter, status_code=200, json={"counter": 1})
        mock_request.delete(url_password_reset_counter, status_code=200, json={})
        mock_request.post(
            f"{TestingConfig.PARTY_URL}/party-api/v1/respondents/123456/password-verification-token",
            status_code=200,
            json={"message": "Successfully added token"},
        )
        response = self.app.get(f"passwords/resend-password-email-expired-token/{token}", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        mock_notify.assert_called_once()
        self.assertTrue("Check your email".encode() in response.data)
