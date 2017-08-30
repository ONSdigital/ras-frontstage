import unittest

import requests_mock

from frontstage import app
from frontstage.exceptions.exceptions import ExternalServiceError
from frontstage.models import RespondentStatus


token = 'TOKEN_ABC'
user_id = 'USER_12345'
party_id = "db036fd7-ce17-40c2-a8fc-932e7c228397"

# Build the mock URL and that is used to validate the email token
url_email_verification = app.config['RAS_PARTY_VERIFY_EMAIL'].format(app.config['RAS_PARTY_SERVICE'], token)
url_resend_verification = app.config['RAS_PARTY_RESEND_VERIFICATION'].format(app.config['RAS_PARTY_SERVICE'], party_id)


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

        response = self.app.get('/register/activate-account/' + token, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 404)
        self.assertTrue('Page not found'.encode() in response.data)

    # Test that the user ends up on the 'Your Link Has Expired' page if they try to access the account activation page
    # with an expired token
    def test_activate_account_expired_token_specified(self, mock_object):
        mock_object.put(url_email_verification, status_code=409, json=self.emailverification_response)

        response = self.app.get('/register/activate-account/' + token, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Expired'.encode() in response.data)

    def test_activate_account_expired_token_no_party_id(self, mock_object):
        del self.emailverification_response['id']
        mock_object.put(url_email_verification, status_code=409, json=self.emailverification_response)

        response = self.app.get('/register/activate-account/' + token, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Oops!'.encode() in response.data)

    # Test that the user ends up on the 'You've activated your account' login page if they try to access the
    # account activation page with a valid, non-expired token
    def test_activate_account_valid_token_specified(self, mock_object):
        mock_object.put(url_email_verification, status_code=200, json=self.emailverification_response)

        response = self.app.get('/register/activate-account/' + token, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Complete'.encode() in response.data)

    def test_activate_account_failed(self, mock_object):
        mock_object.put(url_email_verification, status_code=500, json=self.emailverification_response)

        response = self.app.get('/register/activate-account/' + token, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    def test_activate_account_200_not_active(self, mock_object):
        self.emailverification_response['status'] = RespondentStatus.CREATED.name
        mock_object.put(url_email_verification, status_code=200, json=self.emailverification_response)

        response = self.app.get('/register/activate-account/' + token, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Oops!'.encode() in response.data)

    # ==============EMAIL RE-SENT PAGE ===============

    # Check the content of the 'We've re-sent your email' page
    def test_email_resent(self, mock_object):
        mock_object.get(url_resend_verification, status_code=200)

        response = self.app.get('/register/create-account/email-resent?party_id=' + party_id,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('re-sent'.encode() in response.data)

    def test_email_resent_404(self, mock_object):
        mock_object.get(url_resend_verification, status_code=404)

        response = self.app.get('/register/create-account/email-resent?party_id=' + party_id,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Oops!'.encode() in response.data)

    def test_email_resent_500(self, mock_object):
        mock_object.get(url_resend_verification, status_code=500)

        response = self.app.get('/register/create-account/email-resent?party_id=' + party_id,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    # ============== SIGN IN PAGE WITH 'ACCOUNT ACTIVATED' MESSAGE ===============

    # Check the content of the 'We've re-sent your email' page
    def test_login_account_activated_page(self, mock_object):
        response = self.app.get('/sign-in/?account_activated=True', headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Complete'.encode() in response.data)
