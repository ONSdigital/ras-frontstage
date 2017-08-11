import unittest

import requests_mock

from frontstage import app
from frontstage.models import RespondentStatus


token = 'TOKEN_ABC'
user_id = 'USER_12345'

# Build the mock URL and that is used to validate the email token
url_email_verification = app.config['RAS_PARTY_VERIFY_EMAIL'].format(app.config['RAS_PARTY_SERVICE'], token)


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
            "status": RespondentStatus.ACTIVE.name,
            "id": user_id,
        }

    # ============== ACTIVATE ACCOUNT PAGE ===============

    # Test that the user ends up on the error page if they try to access the account activation page with an
    # invalid (not found) token
    def test_activate_account_invalid_token_specified(self, mock_object):

        mock_object.put(url_email_verification, status_code=404)

        response = self.app.get('/register/activate-account/' + token, headers=self.headers)

        self.assertEqual(response.status_code, 302)

    # Test that the user ends up on the 'Your Link Has Expired' page if they try to access the account activation page
    # with an expired token
    def test_activate_account_expired_token_specified(self, mock_object):

        self.emailverification_response['status'] = RespondentStatus.CREATED.name
        mock_object.put(url_email_verification, status_code=200, json=self.emailverification_response)

        response = self.app.get('/register/activate-account/' + token, headers=self.headers)

        self.assertEqual(response.status_code, 302)

    # Test that the user ends up on the 'You've activated your account' login page if they try to access the
    # account activation page with a valid, non-expired token
    def test_activate_account_valid_token_specified(self, mock_object):
        mock_object.put(url_email_verification, status_code=200, json=self.emailverification_response)

        response = self.app.get('/register/activate-account/' + token, headers=self.headers)

        self.assertEqual(response.status_code, 302)

    # ============== YOUR LINK HAS EXPIRED PAGE ===============

    # Check the content of the 'Your link has expired' page
    def test_link_expired_page(self, mock_object):
        response = self.app.get('/register/create-account/resend-email?user_id=' + user_id, headers=self.headers)

        self.assertEqual(response.status_code, 200)

    # ==============EMAIL RE-SENT PAGE ===============

    # Check the content of the 'We've re-sent your email' page
    def test_email_resent_page(self, mock_object):
        response = self.app.get('/register/create-account/email-resent?user_id=' + user_id, headers=self.headers)

        # TODO check that the email was actually re-sent once the backend functionality has been developed

        self.assertEqual(response.status_code, 200)

    # ============== SIGN IN PAGE WITH 'ACCOUNT ACTIVATED' MESSAGE ===============

    # Check the content of the 'We've re-sent your email' page
    def test_login_account_activated_page(self, mock_object):
        response = self.app.get('/sign-in/?account_activated=True', headers=self.headers)

        self.assertEqual(response.status_code, 200)
