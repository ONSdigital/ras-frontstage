import unittest
from unittest import mock

from jose import JWTError

from frontstage import app
from frontstage.common.session import SessionHandler
from frontstage.common.authorisation import jwt_authorization
from frontstage.exceptions.exceptions import JWTValidationError


valid_jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZWZyZXNoX3Rva2VuIjoiNmY5NjM0ZGEtYTI3ZS00ZDk3LWJhZjktNjNjO" \
                  "GRjY2IyN2M2IiwiYWNjZXNzX3Rva2VuIjoiMjUwMDM4YzUtM2QxOS00OGVkLThlZWMtODFmNTQyMDRjNDE1Iiwic2NvcGUiOls" \
                  "iIl0sImV4cGlyZXNfYXQiOjE4OTM0NTk2NjEuMCwidXNlcm5hbWUiOiJ0ZXN0dXNlckBlbWFpbC5jb20iLCJyb2xlIjoicmVzc" \
                  "G9uZGVudCIsInBhcnR5X2lkIjoiZGIwMzZmZDctY2UxNy00MGMyLWE4ZmMtOTMyZTdjMjI4Mzk3In0.hh9sFpiPA-O8kugpDi3" \
                  "_GSDnxWh5rz2e5GQuBx7kmLM"
expired_jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZWZyZXNoX3Rva2VuIjoiNGYzMmI0YjQtNGUwYS00NTUyLThiOTYtODI" \
                    "zNjRjODk2ZjFiIiwiYWNjZXNzX3Rva2VuIjoiMWMxNGJhOGMtOTlhMS00NjBjLTllYmUtMTFlY2U4NGY1ZTAzIiwic2NvcGU" \
                    "iOlsiIl0sImV4cGlyZXNfYXQiOjk0NjY4ODQ2MS4wLCJ1c2VybmFtZSI6InRlc3R1c2VyQGVtYWlsLmNvbSIsInJvbGUiOiJ" \
                    "yZXNwb25kZW50IiwicGFydHlfaWQiOiJkYjAzNmZkNy1jZTE3LTQwYzItYThmYy05MzJlN2MyMjgzOTcifQ.ro95XUJ2gqgz" \
                    "7ecF2r3guSi-kh4wI_XYTgUF8IZFHDA"
no_expiry_jwt = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZWZyZXNoX3Rva2VuIjoiMGE0NGQ4YzYtZWEzYy00ZTMzLTg4MDctNjJkYmViOTN' \
                'lMzZhIiwiYWNjZXNzX3Rva2VuIjoiYWVmZTkyYjAtNTYxYi00ZWM0LTljNTYtMTYwZGZhNGIzNzY0Iiwicm9sZSI6InJlc3BvbmRlbnQ' \
                'iLCJwYXJ0eV9pZCI6IjU2NWJjMDc5LWVkMDItNDk0MS04ODgyLWRhZTZmYzE4NWEzZCJ9.unskbEm5dWQfCTvE25cxrOhAf1_Ii8ZXiL' \
                'hBioQq8OE'


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
