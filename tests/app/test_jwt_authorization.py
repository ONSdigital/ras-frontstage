import unittest
from unittest import mock

from jose import JWTError

from frontstage import app
from frontstage.common.session import SessionHandler
from frontstage.common.authorisation import jwt_authorization
from frontstage.exceptions.exceptions import JWTValidationError


valid_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NfdG9rZW4iOiIyMGNkM2RhOC05ODZhLTQzNzAtYTEwOC01Y2M1Y2NlOWF" \
            "jOWIiLCJyb2xlIjoicmVzcG9uZGVudCIsInJlZnJlc2hfdG9rZW4iOiI3NmZmN2Q1NC0yYmQ4LTQwMTgtOTg2OS05NzBjNDk4NzZmOWI" \
            "iLCJwYXJ0eV9pZCI6ImY5NTZlOGFlLTZlMGYtNDQxNC1iMGNmLWEwN2MxYWEzZTM3YiIsImV4cGlyZXNfYXQiOjE1MTcyMjk4NDIuMDA" \
            "2MjQ0fQ.ybIm2NpOAmNEVne70MVaXOdcGz2NCIpbeB9YVcd4M2I"
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

    def test_jwt_authorization_no_JWT(self):
        request = mock.MagicMock()

        with self.assertRaises(JWTValidationError):
            self.decorator_test(request)

    def test_jwt_authorization_expired_JWT(self):
        self.session.create_session(expired_jwt)
        request = mock.MagicMock(cookies={"authorization": self.session.session_key})

        with self.assertRaises(JWTValidationError):
            self.decorator_test(request)

    def test_jwt_authorization_no_exipry(self):
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
