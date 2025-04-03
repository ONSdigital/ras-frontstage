import unittest
from unittest import mock

from werkzeug.exceptions import Unauthorized

from frontstage import app
from frontstage.common.authorisation import (
    EXPIRES_IN_MISSING_FROM_PAYLOAD,
    JWT_DATE_EXPIRED,
    JWT_DECODE_ERROR,
    NO_AUTHORIZATION_COOKIE,
    NO_ENCODED_JWT,
    jwt_authorization,
)
from frontstage.common.session import Session
from frontstage.exceptions.exceptions import JWTTimeoutError, JWTValidationError

valid_jwt = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwYXJ0eV9pZCI6InRlc3QiLCJyb2xlIjoicmVzcG9uZGVudCIsInVucmVhZF9"
    "tZXNzYWdlX2NvdW50Ijp7InZhbHVlIjoxLCJyZWZyZXNoX2luIjozMjUwMzcyNTY4MTAwMH0sImV4cGlyZXNfaW4iOjMyNTAzNzI"
    "1NjgxMDAwfQ.8lZiYTzjFuPb6sgYJne88Qua8ozAjnSrZRgoXN6qKic"
)

in_valid_jwt = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwYXJ0eV9pZCI6InRlc3QiLCJyb2xlIjoicmVzcG9uZGVudCIsInVucmVhZF9"
    "tZXNzYWdlX2NvdW50Ijp7InZhbHVlIjoxLCJyZWZyZXNoX2luIjozMjUwMzcyNTY4MTAwMH0sImV4cGlyZXNfaW4iOjMyNTAzNzI"
    "1NjgxMDAwfQ"
)

expired_jwt = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwYXJ0eV9pZCI6InRlc3QiLCJyb2xlIjoicmVzcG9uZGVudCIsInVucmVhZF"
    "9tZXNzYWdlX2NvdW50Ijp7InZhbHVlIjoxLCJyZWZyZXNoX2luIjoxNTg3OTU1ODAzLjk4ODM4M30sImV4cGlyZXNfaW4iOjE1O"
    "Dc5NTkxMDMuOTI1MDg4fQ.nntdPMRSQFjCAax0J0Iez1l5BbtqE8x617yWcN_zhKY"
)

no_expires_in_jwt = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwYXJ0eV9pZCI6InRlc3QiLCJyb2xlIjoicmVzcG9uZGVudCIsInVucmVh"
    "ZF9tZXNzYWdlX2NvdW50Ijp7InZhbHVlIjoxLCJyZWZyZXNoX2luIjoxNjg3OTU1ODAzLjk4ODM4M319.JHUjhH4D00vIFCrC"
    "YCyUMoxQCx0cTIPdsUVglKdNajk"
)


class TestJWTAuthorization(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.party_id = "test"
        self.session = Session.from_party_id(self.party_id)

    @staticmethod
    def decorator_test(request):
        @jwt_authorization(request)
        def test_function(_):
            pass

        test_function()

    def test_jwt_authorization_success(self):
        # Given a valid JWT and authorization cookie
        self._update_session_token()
        request = mock.MagicMock(cookies={"authorization": self.session.session_key})

        # When the jwt_authorization decorator is exercised
        # Then the function runs without exceptions and the test is considered as passed
        self.decorator_test(request)

    def test_jwt_authorization_no_cookie(self):
        # Given the respondent doesnt have an authorization cookie
        request = mock.MagicMock(cookies={})

        # When the jwt_authorization decorator is exercised
        # Then the function raises an Unauthorized, NO_AUTHORIZATION_COOKIE exception
        with self.assertRaises(Unauthorized) as e:
            self.decorator_test(request)
        self.assertEqual(e.exception.description, NO_AUTHORIZATION_COOKIE)

    def test_jwt_authorization_no_encoded_jwt_for_session(self):
        # Given the respondent has an authorization cookie, but the key doesn't match a session in redis
        request = mock.MagicMock(cookies={"authorization": "incorrect_session_key"})

        # When the jwt_authorization decorator is exercised
        # Then the function raises an Unauthorized, NO_ENCODED_JWT exception
        with self.assertRaises(Unauthorized) as e:
            self.decorator_test(request)
        self.assertEqual(e.exception.description, NO_ENCODED_JWT)

    def test_jwt_authorization_expired(self):
        # Given a valid JWT and authorization cookie, but the token has expired
        self._update_session_token(expired_jwt)
        request = mock.MagicMock(cookies={"authorization": self.session.session_key})

        # When the jwt_authorization decorator is exercised
        # Then the function raises an Unauthorized, JWT_DATE_EXPIRED exception
        with self.assertRaises(JWTTimeoutError) as e:
            self.decorator_test(request)
        self.assertEqual(e.exception.message, f"{JWT_DATE_EXPIRED} {self.party_id}")

    def test_jwt_authorization_no_expiry_in_payload(self):
        # Given a valid authorization cookie, but invalid JWT where the expiry_in key is missing from the payload
        self._update_session_token(no_expires_in_jwt)
        request = mock.MagicMock(cookies={"authorization": self.session.session_key})

        # When the jwt_authorization decorator is exercised
        # Then the function raises an JWTValidationError exception
        with self.assertRaises(JWTValidationError) as e:
            self.decorator_test(request)
        self.assertEqual(e.exception.message, f"{EXPIRES_IN_MISSING_FROM_PAYLOAD} {self.party_id}")

    def test_jwt_authorization_decode_failure(self):
        # Given a valid authorization cookie, but invalid JWT where the decode step fails
        self._update_session_token(in_valid_jwt)
        request = mock.MagicMock(cookies={"authorization": self.session.session_key})

        # When the jwt_authorization decorator is exercised
        # Then the function raises an JWTValidationError exception
        with self.assertRaises(JWTValidationError) as e:
            self.decorator_test(request)
        self.assertEqual(e.exception.message, f"{JWT_DECODE_ERROR} {self.session.session_key}")

    def _update_session_token(self, token=valid_jwt):
        self.session.encoded_jwt_token = token
        self.session.set()
