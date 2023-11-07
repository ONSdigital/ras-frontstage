import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import requests_mock
from bs4 import BeautifulSoup
from freezegun import freeze_time
from requests.exceptions import ConnectionError

from frontstage import app
from frontstage.exceptions.exceptions import (
    ApiError,
    JWTTimeoutError,
    JWTValidationError,
)
from frontstage.views.sign_in.logout import SIGN_OUT_GUIDANCE
from tests.integration.mocked_services import (
    encoded_jwt_token,
    url_auth_token,
    url_banner_api,
)

TIME_TO_FREEZE = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


class TestErrorHandlers(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.sign_in_form = {"username": "testuser@email.com", "password": "password"}
        os.environ["APP_SETTINGS"] = "TestingConfig"

    @requests_mock.mock()
    def test_not_found_error(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get("/not-a-url", follow_redirects=True)

        self.assertEqual(response.status_code, 404)
        self.assertTrue("not found".encode() in response.data)

    # Use bad data to raise an uncaught exception
    @requests_mock.mock()
    def test_server_error(self, mock_request):
        mock_request.post(url_auth_token, status_code=200)
        mock_request.get(url_banner_api, status_code=404)

        response = self.app.post("/sign-in/", data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue("An error has occurred".encode() in response.data)

    @requests_mock.mock()
    def test_api_error(self, mock_request):
        response_mock = MagicMock()
        logger_mock = MagicMock()
        mock_request.post(url_auth_token, exc=ApiError(logger_mock, response_mock))
        mock_request.get(url_banner_api, status_code=404)

        response = self.app.post("sign-in", data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue("An error has occurred".encode() in response.data)

    @requests_mock.mock()
    def test_connection_error(self, mock_request):
        mock_exception_request = MagicMock()
        mock_request.post(url_auth_token, exc=ConnectionError(request=mock_exception_request))
        mock_request.get(url_banner_api, status_code=404)

        response = self.app.post("sign-in", data=self.sign_in_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue("An error has occurred".encode() in response.data)

    @requests_mock.mock()
    def test_jwt_validation_error(self, mock_request):
        mock_request.post(url_auth_token, exc=JWTValidationError(message="Error message"))
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.post("sign-in", data=self.sign_in_form, follow_redirects=True)
        self.assertEqual(response.status_code, 500)

    @requests_mock.mock()
    def test_jwt_timeout_error(self, mock_request):
        mock_request.post(url_auth_token, exc=JWTTimeoutError(message="Error message"))
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.post("sign-in", data=self.sign_in_form, follow_redirects=True)
        self.assertEqual(response.status_code, 401)

    def test_csrf_token_missing(self):
        # Given csrf is enabled
        app.config["WTF_CSRF_ENABLED"] = True

        # When the respondent signs in without a csrf token in the form data
        response = self.app.post("/sign-in/", data=self.sign_in_form, follow_redirects=True)
        app.config["WTF_CSRF_ENABLED"] = False

        # Then a 400 is returned
        self.assertEqual(response.status_code, 400)

    def test_csrf_token_invalid(self):
        # Given csrf is enabled
        app.config["WTF_CSRF_ENABLED"] = True

        # When the respondent signs in with an invalid csrf token in the form data
        invalid_csrf_token = (
            "IjY1MDRlYTQ3NWE4MTRlOTVmZGI5NWM2YTY1NDc5ZjMwN2E5NTc3OWEi.Y7F1wA.Z-9JSB8GoweG4Q2NJsjZnJasdF4"
        )
        sign_in_details = {"username": "testuser@email.com", "password": "password", "csrf_token": invalid_csrf_token}
        response = self.app.post("/sign-in/", data=sign_in_details, follow_redirects=True)
        app.config["WTF_CSRF_ENABLED"] = False

        # Then a 400 is returned
        self.assertEqual(response.status_code, 400)

    @freeze_time(TIME_TO_FREEZE)
    def test_csrf_expired_without_auth_cookie(self):
        # Given csrf is enabled
        app.config["WTF_CSRF_ENABLED"] = True

        # When the respondent signs in with an expired csrf token and without an authorization cookie
        csrf_timeout_response = self._get_csrf_timeout_response()

        # Then a 400 is returned
        self.assertEqual(csrf_timeout_response.status_code, 400)

    @patch("redis.StrictRedis.get")
    def test_csrf_expired_with_auth_cookie(self, redis_get):
        # Given csrf is enabled
        app.config["WTF_CSRF_ENABLED"] = True

        # When the respondent signs in with an expired csrf token but does have a valid authorization cookie
        self.app.set_cookie("authorization", "session_key")
        redis_get.return_value = encoded_jwt_token
        csrf_timeout_response = self._get_csrf_timeout_response()

        # Then a 200 is returned and notified they have been signed out
        self.assertEqual(csrf_timeout_response.status_code, 200)
        self.assertTrue(SIGN_OUT_GUIDANCE.encode() in csrf_timeout_response.data)

    def _get_csrf_timeout_response(self):
        csrf_value = self._get_csrf_value_from_html(self.app.get("/sign-in/").data)
        sign_in_details = {"username": "testuser@email.com", "password": "password", "csrf_token": csrf_value}
        future_time = TIME_TO_FREEZE + timedelta(minutes=61)
        with freeze_time(future_time):
            response = self.app.post("/sign-in/", data=sign_in_details, follow_redirects=True)
        app.config["WTF_CSRF_ENABLED"] = False
        return response

    @staticmethod
    def _get_csrf_value_from_html(data):
        soup = BeautifulSoup(data, "html.parser")
        return soup.find("input", {"id": "csrf_token"}).get("value")
