import unittest
from unittest.mock import MagicMock, Mock, patch

import requests_mock
from itsdangerous import SignatureExpired

from config import TestingConfig
from frontstage import app
from frontstage.common import verification
from frontstage.controllers import party_controller
from frontstage.exceptions.exceptions import ApiError
from tests.integration.mocked_services import (
    respondent_party,
    token,
    url_banner_api,
    url_get_respondent_by_email,
    url_password_change,
    url_reset_password_request,
    url_verify_token,
)

encoded_valid_email = "ImV4YW1wbGVAZXhhbXBsZS5jb20i.vMOqeMafWQpuxbUBRyRs29T0vDI"
encoded_invalid_email = "abcd"

respondent_id = respondent_party["id"]

url_resend_password_email_expired_token = (
    f"{TestingConfig.PARTY_URL}/party-api/v1" f"/resend-password-email-expired-token/{token}",
)

url_password_reset_counter = (
    f"{app.config['PARTY_URL']}/party-api/v1/respondents/{respondent_id}/password-reset-counter"
)

response_mock = MagicMock()
logger_mock = MagicMock()

respondent_party_without_token = dict(respondent_party)
respondent_party_without_token["password_verification_token"] = None


class TestPasswords(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        self.email_form = {"email_address": respondent_party["emailAddress"]}
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
        mock_request.post(url_reset_password_request)
        mock_request.get(url_get_respondent_by_email, json=respondent_party_without_token)
        mock_request.get(url_password_reset_counter, json={"counter": 0})
        mock_request.delete(url_password_reset_counter, json={})
        mock_request.post(
            f"{TestingConfig.PARTY_URL}/party-api/v1/respondents/{respondent_id}/password-verification-token",
            status_code=200,
            json={"message": "Successfully added token"},
        )

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        mock_notify.assert_called_once()
        self.assertTrue("Check your email".encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.notify_controller.NotifyGateway.request_to_notify")
    @patch.object(verification, "decode_email_token", Mock(return_value=respondent_party["emailAddress"]))
    @patch.object(verification, "generate_email_token", Mock(return_value=token))
    def test_forgot_password_post_success_with_token_and_counter(self, mock_request, mock_notify):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_reset_password_request)
        mock_request.get(url_get_respondent_by_email, json=respondent_party)
        mock_request.get(url_password_reset_counter, json={"counter": 1})
        mock_request.delete(url_password_reset_counter, json={})
        mock_request.post(
            f"{TestingConfig.PARTY_URL}/party-api/v1/respondents/{respondent_id}/password-verification-token",
            status_code=200,
            json={"message": "Successfully added token"},
        )
        mock_request.get(url_get_respondent_by_email, json=respondent_party)
        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        mock_notify.assert_called_once()
        self.assertTrue("Check your email".encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.notify_controller.NotifyGateway.request_to_notify")
    @patch.object(verification, "decode_email_token", Mock(return_value=respondent_party["emailAddress"]))
    @patch.object(verification, "generate_email_token", Mock(return_value=token))
    def test_forgot_password_post_success_with_1_try_left(self, mock_request, mock_notify):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(
            url_reset_password_request,
        )
        mock_request.get(url_get_respondent_by_email, json=respondent_party_without_token)
        mock_request.get(url_password_reset_counter, json={"counter": 4})
        mock_request.post(
            f"{TestingConfig.PARTY_URL}/party-api/v1/respondents/{respondent_id}/password-verification-token",
            json={"message": "Successfully added token"},
        )
        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        mock_notify.assert_called_once()
        self.assertTrue("You have 1 try left to reset your password".encode() in response.data)
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
        mock_request.post(url_reset_password_request)
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
        mock_request.get(url_get_respondent_by_email, json=respondent_party)
        mock_request.delete(
            f"{TestingConfig.PARTY_URL}/party-api/v1/respondents/{respondent_id}/password-verification-token/{token}",
            json={"message": "Successfully removed token"},
        )
        mock_request.delete(url_password_reset_counter, status_code=200)
        response = self.app.post(f"passwords/reset-password/{token}", data=password_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Your password has been changed".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_respondent_not_found(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_get_respondent_by_email, status_code=404, json={})

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
        mock_request.get(url_verify_token)
        password_form = {"password": "Gizmo008!", "password_confirm": "Gizmo007!"}
        with app.app_context():
            token = verification.generate_email_token("test.com")
        mock_request.get(
            url_get_respondent_by_email,
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
            json={"firstName": "Bob", "id": "123456", "password_verification_token": token},
        )
        response = self.app.post(f"passwords/reset-password/{token}", data=password_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Your password doesn't meet the requirements".encode() in response.data)

    @requests_mock.mock()
    def test_reset_password_no_password(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_verify_token)
        password_form = {}
        with app.app_context():
            token = verification.generate_email_token("test.com")
        mock_request.get(
            url_get_respondent_by_email,
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

        response = self.app.post(f"passwords/reset-password/{token}", data=password_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue("An error has occurred".encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.notify_controller.NotifyGateway.request_to_notify")
    @patch.object(verification, "decode_email_token", Mock(return_value=respondent_party["emailAddress"]))
    @patch.object(verification, "generate_email_token", Mock(return_value=token))
    def test_resend_verification_email_using_expired_token(self, mock_request, mock_notify):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get("http://localhost:8081/party-api/v1/respondents/email", json=respondent_party_without_token)
        mock_request.get(url_password_reset_counter, json={"counter": 0})
        mock_request.delete(url_password_reset_counter)
        mock_request.post(
            f"{TestingConfig.PARTY_URL}/party-api/v1/respondents/{respondent_id}/password-verification-token",
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
    @patch.object(verification, "decode_email_token", Mock(return_value=respondent_party["emailAddress"]))
    def test_too_many_reset_attempts(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_reset_password_request)
        mock_request.get(url_get_respondent_by_email, json=respondent_party)
        mock_request.get(url_password_reset_counter, json={"counter": 5})
        mock_request.post(
            f"{TestingConfig.PARTY_URL}/party-api/v1/respondents/{respondent_id}/password-verification-token",
            json={"message": "Successfully added token"},
        )

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("You've tried to reset your password too many times".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.notify_controller.NotifyGateway.request_to_notify")
    @patch.object(
        verification,
        "decode_email_token",
        Mock(side_effect=[SignatureExpired("Test"), respondent_party["emailAddress"]]),
    )
    @patch.object(verification, "generate_email_token", Mock(return_value=token))
    def test_reset_password_reset_counter(self, mock_request, mock_notify):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_reset_password_request)
        mock_request.get(url_password_reset_counter, json={"counter": 5})
        mock_request.delete(url_password_reset_counter, json={})
        mock_request.get(url_get_respondent_by_email, json=respondent_party)
        mock_request.post(
            f"{TestingConfig.PARTY_URL}/party-api/v1/respondents/{respondent_id}/password-verification-token",
            json={"message": "Successfully added token"},
        )

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Check your email".encode() in response.data)
        mock_notify.assert_called_once()

    @requests_mock.mock()
    @patch("frontstage.controllers.notify_controller.NotifyGateway.request_to_notify")
    @patch.object(verification, "decode_email_token", Mock(return_value=respondent_party["emailAddress"]))
    @patch.object(verification, "generate_email_token", Mock(return_value=token))
    def test_resend_verification_email_with_null_token_and_counter_not_0(self, mock_request, mock_notify):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(
            "http://localhost:8081/party-api/v1/respondents/email",
            json=respondent_party_without_token,
        )
        mock_request.get(url_password_reset_counter, json={"counter": 1})
        mock_request.delete(url_password_reset_counter)
        mock_request.post(
            f"{TestingConfig.PARTY_URL}/party-api/v1/respondents/{respondent_id}/password-verification-token",
            json={"message": "Successfully added token"},
        )

        response = self.app.get(f"passwords/resend-password-email-expired-token/{token}", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Check your email".encode() in response.data)
        mock_notify.assert_called_once()

    @requests_mock.mock()
    @patch("frontstage.controllers.notify_controller.NotifyGateway.request_to_notify")
    @patch.object(verification, "decode_email_token", Mock(return_value=respondent_party["emailAddress"]))
    @patch.object(verification, "generate_email_token", Mock(return_value=token))
    def test_resend_verification_email_with_empty_token_and_counter_not_0(self, mock_request, mock_notify):
        mock_request.get(url_banner_api, status_code=404)
        respondent_party_with_empty_token = dict(respondent_party_without_token)
        respondent_party_with_empty_token["password_verification_token"] = ""
        mock_request.get("http://localhost:8081/party-api/v1/respondents/email", json=respondent_party_with_empty_token)
        mock_request.get(url_password_reset_counter, json={"counter": 1})
        mock_request.post(
            f"{TestingConfig.PARTY_URL}/party-api/v1/respondents/{respondent_id}/password-verification-token",
            json={"message": "Successfully added token"},
        )

        response = self.app.get(f"passwords/resend-password-email-expired-token/{token}", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Check your email".encode() in response.data)
        mock_notify.assert_called_once()

    @requests_mock.mock()
    @patch("frontstage.controllers.notify_controller.NotifyGateway.request_to_notify")
    @patch.object(
        verification,
        "decode_email_token",
        Mock(side_effect=[SignatureExpired("Test"), respondent_party["emailAddress"]]),
    )
    @patch.object(verification, "generate_email_token", Mock(return_value=token))
    def test_forgot_password_post_success_with_expired_signature(self, mock_request, mock_notify):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_reset_password_request)
        mock_request.get(url_password_reset_counter, json={"counter": 1})
        mock_request.delete(url_password_reset_counter, json={})
        mock_request.get(url_get_respondent_by_email, json=respondent_party)
        mock_request.post(
            f"{TestingConfig.PARTY_URL}/party-api/v1/respondents/{respondent_id}/password-verification-token",
            json={"message": "Successfully added token"},
        )

        response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Check your email".encode() in response.data)
        mock_notify.assert_called_once()

    @requests_mock.mock()
    @patch.object(verification, "decode_email_token", Mock(side_effect=SignatureExpired("Test")))
    @patch.object(
        party_controller, "reset_password_reset_counter", Mock(side_effect=ApiError(logger_mock, response_mock))
    )
    def test_reset_password_reset_counter_party_fail(self, mock_request):
        with app.app_context():
            mock_request.get(url_banner_api, status_code=404)
            mock_request.post(url_reset_password_request)
            mock_request.get(url_password_reset_counter, json={"counter": 1})
            mock_request.get(url_get_respondent_by_email, json=respondent_party)
            mock_request.post(
                f"{TestingConfig.PARTY_URL}/party-api/v1/respondents/{respondent_id}/password-verification-token"
            )

            response = self.app.post("passwords/forgot-password", data=self.email_form, follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertTrue("Something went wrong".encode() in response.data)
