import unittest
from unittest import mock

from jose import JWTError

from frontstage import app
from frontstage.common.authorisation import jwt_authorization
from frontstage.common.session import SessionHandler
from frontstage.exceptions.exceptions import JWTValidationError

valid_jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoicmVzcG9uZGVudCIsImFjY2Vzc190b2tlbiI6ImI5OWIyMjA0LWYxM" \
            "DAtNDcxZS1iOTQ1LTIyN2EyNmVhNjljZCIsInJlZnJlc2hfdG9rZW4iOiIxZTQyY2E2MS02ZDBkLTQxYjMtODU2Yy02YjhhMDhlYmI" \
            "yZTMiLCJleHBpcmVzX2F0IjoxNzM4MTU4MzI4LjAsInBhcnR5X2lkIjoiZjk1NmU4YWUtNmUwZi00NDE0LWIwY2YtYTA3YzFhYTNlM" \
            "zdiIn0.7W9yikGtX2gbKLclxv-dajcJ2NL0Nb_HDVqHrCrYvQE"
expired_jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZWZyZXNoX3Rva2VuIjoiNGYzMmI0YjQtNGUwYS00NTUyLThiOTYtODIzNjRjO" \
              "Dk2ZjFiIiwiYWNjZXNzX3Rva2VuIjoiMWMxNGJhOGMtOTlhMS00NjBjLTllYmUtMTFlY2U4NGY1ZTAzIiwic2NvcGUiOlsiIl0sImV" \
              "4cGlyZXNfYXQiOjk0NjY4ODQ2MS4wLCJ1c2VybmFtZSI6InRlc3R1c2VyQGVtYWlsLmNvbSIsInJvbGUiOiJyZXNwb25kZW50Iiwic" \
              "GFydHlfaWQiOiJkYjAzNmZkNy1jZTE3LTQwYzItYThmYy05MzJlN2MyMjgzOTcifQ.ro95XUJ2gqgz7ecF2r3guSi-kh4wI_XYTgUF" \
              "8IZFHDA"
no_expiry_jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZWZyZXNoX3Rva2VuIjoiMGE0NGQ4YzYtZWEzYy00ZTMzLTg4MDctNjJkYmV" \
                "iOTNlMzZhIiwiYWNjZXNzX3Rva2VuIjoiYWVmZTkyYjAtNTYxYi00ZWM0LTljNTYtMTYwZGZhNGIzNzY0Iiwicm9sZSI6InJlc3B" \
                "vbmRlbnQiLCJwYXJ0eV9pZCI6IjU2NWJjMDc5LWVkMDItNDk0MS04ODgyLWRhZTZmYzE4NWEzZCJ9.unskbEm5dWQfCTvE25cxrO" \
                "hAf1_Ii8ZXiLhBioQq8OE"


class TestJWTAuthorization(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.session = SessionHandler()

    def tearDown(self):
        self.session.delete_session(self.session.session_key)

    @staticmethod
    def decorator_test(request):
        @jwt_authorization(request)
        def test_function(session):
            pass
        test_function()

    def test_jwt_authorization_success(self):
        self.session.create_session(valid_jwt)
        request = mock.MagicMock(cookies={"authorization": self.session.session_key})

        # If this function runs without exceptions the test is considered passed
        self.decorator_test(request)

    def test_jwt_authorization_expired_jwt(self):
        self.session.create_session(expired_jwt)
        request = mock.MagicMock(cookies={"authorization": self.session.session_key})

        with self.assertRaises(JWTValidationError):
            self.decorator_test(request)

    def test_jwt_authorization_no_expiry(self):
        self.session.create_session(no_expiry_jwt)
        request = mock.MagicMock(cookies={"authorization": self.session.session_key})

        with self.assertRaises(JWTValidationError):
            self.decorator_test(request)

    @mock.patch('frontstage.common.authorisation.decode')
    def test_jwt_authorization_decode_failure(self, mock_decode):
        self.session.create_session(valid_jwt)
        request = mock.MagicMock(cookies={"authorization": self.session.session_key})
        mock_decode.side_effect = JWTError

        with self.assertRaises(JWTValidationError):
            self.decorator_test(request)
