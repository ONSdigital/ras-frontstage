import unittest
from app.application import app
from app.config import Config
import requests_mock

token = 'TOKEN_ABC'
user_id = 'USER_12345'

# Build the mock URL and that is used to validate the email token
url_email_verification = Config.API_GATEWAY_PARTY_URL + 'emailverification/{}'.format(token)

@requests_mock.mock()
class TestAccountActivation(unittest.TestCase):
    """Test case for application endpoints and functionality"""

    def setUp(self):
        self.app = app.test_client()
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
            }
        self.emailverification_response = {
            "token": token,
            "active": True,
            "userId": user_id
        }

    # ============== ACTIVATE ACCOUNT PAGE ===============

    # Test that the user ends up on the error page if they try to access the account activation page without a token
    def test_activate_account_no_token_specified(self, mock_object):
        response = self.app.get('/activate-account', headers=self.headers)

        # Token not specified so user should be redirected to the error page
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            bytes('You should be redirected automatically to target URL', encoding='UTF-8') in response.data)
        self.assertTrue('/error'.encode() in response.data)

    # Test that the user ends up on the error page if they try to access the account activation page with an
    # invalid (not found) token
    def test_activate_account_invalid_token_specified(self, mock_object):

        mock_object.post(url_email_verification, status_code=404)

        response = self.app.get('/activate-account?t=' + token, headers=self.headers)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            bytes('You should be redirected automatically to target URL', encoding='UTF-8') in response.data)
        self.assertTrue('/error'.encode() in response.data)

    # Test that the user ends up on the 'Your Link Has Expired' page if they try to access the account activation page
    # with an expired token
    def test_activate_account_expired_token_specified(self, mock_object):

        self.emailverification_response['active'] = False
        mock_object.post(url_email_verification, status_code=200, json=self.emailverification_response)

        response = self.app.get('/activate-account?t=' + token, headers=self.headers)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            bytes('You should be redirected automatically to target URL', encoding='UTF-8') in response.data)
        self.assertTrue(('/create-account/resend-email?user_id=' + user_id).encode() in response.data)

    # Test that the user ends up on the 'You've activated your account' login page if they try to access the
    # account activation page with a valid, non-expired token
    def test_activate_account_valid_token_specified(self, mock_object):
        mock_object.post(url_email_verification, status_code=200, json=self.emailverification_response)

        response = self.app.get('/activate-account?t=' + token, headers=self.headers)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            bytes('You should be redirected automatically to target URL', encoding='UTF-8') in response.data)
        self.assertTrue('/sign-in?account_activated=True'.encode() in response.data)

    # ============== YOUR LINK HAS EXPIRED PAGE ===============

    # Check the content of the 'Your link has expired' page
    def test_link_expired_page(self, mock_object):
        response = self.app.get('create-account/resend-email?user_id=' + user_id, headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes('Your link has expired', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('Request another email with a new link', encoding='UTF-8') in response.data)

    # ==============EMAIL RE-SENT PAGE ===============

    # Check the content of the 'We've re-sent your email' page
    def test_email_resent_page(self, mock_object):
        response = self.app.get('create-account/email-resent?user_id=' + user_id, headers=self.headers)

        # TODO check that the email was actually re-sent once the backend functionality has been developed

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes('We\'ve re-sent your email', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('Please check your email', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('Help with email', encoding='UTF-8') in response.data)

    # ============== SIGN IN PAGE WITH 'ACCOUNT ACTIVATED' MESSAGE ===============

    # Check the content of the 'We've re-sent your email' page
    def test_login_account_activated_page(self, mock_object):
        response = self.app.get('sign-in?account_activated=True', headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes('You\'ve activated your account', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('You may now sign in', encoding='UTF-8') in response.data)
        self.assertTrue(bytes('SIGN_IN_BUTTON', encoding='UTF-8') in response.data)
