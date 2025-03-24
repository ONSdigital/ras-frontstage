import unittest

import requests_mock

from frontstage import app
from tests.integration.mocked_services import url_banner_api


class TestSignOutHelp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie("authorization", "session_key")

    @requests_mock.mock()
    def test_sign_out_help_page(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get("/help")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Help".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("Information about the Office for National Statistics (ONS)".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    def test_sign_out_help_post(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        form = {"option": "info-ons"}
        response = self.app.post("/help", data=form, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Information about the Office for National Statistics (ONS)".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("Who is the Office for National Statistics (ONS)?".encode(), response.data)
        self.assertIn("How do you keep my data safe?".encode(), response.data)
        self.assertIn("Something else".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    def test_sign_out_help_post_select_option(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        form = {}
        response = self.app.post("/help", data=form, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("At least one option should be selected.".encode(), response.data)
        self.assertIn("You need to choose an option".encode(), response.data)

    @requests_mock.mock()
    def test_sign_out_help_post_ons_info_option_needs_to_be_selected(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        form = {}
        response = self.app.post("/help/info-ons", data=form, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("At least one option should be selected.".encode(), response.data)
        self.assertIn("You need to choose an option".encode(), response.data)

    @requests_mock.mock()
    def test_sign_out_help_post_who_is_ons(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        form = {"option": "ons"}
        response = self.app.post("/help/info-ons", data=form, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Who is the Office for National Statistics (ONS)?".encode(), response.data)
        self.assertIn("Sign in to your account".encode(), response.data)
        self.assertIn("If you are having problems signing in, please ".encode(), response.data)
        self.assertNotIn(
            'Send a <a id="contact_us" href="/contact-us/send-message">secure message</a>'.encode(), response.data
        )

    @requests_mock.mock()
    def test_sign_out_help_post_ons_info_data_safe(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        form = {"option": "data"}
        response = self.app.post("/help/info-ons", data=form, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("How do you keep my data safe?".encode(), response.data)
        self.assertNotIn("Continue".encode(), response.data)
        self.assertNotIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    def test_sign_out_help_post_ons_info_something_else(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        form = {"option": "info-something-else"}
        response = self.app.post("/help/info-ons", data=form, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Information about the Office for National Statistics (ONS)".encode(), response.data)
        self.assertIn("Need more information?".encode(), response.data)
        self.assertNotIn("Continue".encode(), response.data)
        self.assertNotIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    def test_sign_out_help_with_my_password(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        form = {"option": "password"}
        response = self.app.post("/help", data=form, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Help with my password".encode(), response.data)
        self.assertIn("Choose an option".encode(), response.data)
        self.assertIn("I have not received the password reset email".encode(), response.data)
        self.assertIn("I cannot reset my password using the link".encode(), response.data)
        self.assertIn("My new password is not being accepted".encode(), response.data)
        self.assertIn("Something else".encode(), response.data)
        self.assertIn("Continue".encode(), response.data)
        self.assertIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    def test_sign_out_help_with_password_post_ons_info_option_needs_to_be_selected(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        form = {}
        response = self.app.post("/help/help-with-my-password", data=form, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("At least one option should be selected.".encode(), response.data)
        self.assertIn("You need to choose an option".encode(), response.data)

    @requests_mock.mock()
    def test_sign_out_help_with_password_post_not_received_password_reset_email(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        form = {"option": "reset-email"}
        response = self.app.post("/help/help-with-my-password", data=form, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("I have not received the password reset email".encode(), response.data)
        self.assertIn(
            "that the email address ons.surveys@notifications.service.gov.uk is added to your list of "
            "approved senders".encode(),
            response.data,
        )
        self.assertNotIn("Continue".encode(), response.data)
        self.assertNotIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    def test_sign_out_help_with_password_is_not_being_accepted(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        form = {"option": "password-not-accept"}
        response = self.app.post("/help/help-with-my-password", data=form, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("My new password isn't being accepted".encode(), response.data)
        self.assertIn(
            "We recommend that you enter your password directly into the password box rather than copy and "
            "paste it in. This will prevent you pasting any hidden or special characters.".encode(),
            response.data,
        )
        self.assertNotIn("Continue".encode(), response.data)
        self.assertNotIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    def test_sign_out_help_with_password_reset(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        form = {"option": "reset-password"}
        response = self.app.post("/help/help-with-my-password", data=form, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("I cannot reset my password using the link".encode(), response.data)
        self.assertIn(
            "If 72 hours have passed since you reset, you should reset your password again.".encode(), response.data
        )
        self.assertNotIn("Continue".encode(), response.data)
        self.assertNotIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    def test_sign_out_help_with_password_something_else(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        form = {"option": "password-something-else"}
        response = self.app.post("/help/help-with-my-password", data=form, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Help with my password".encode(), response.data)
        self.assertIn("If you are having problems signing in, please".encode(), response.data)
        self.assertNotIn("Continue".encode(), response.data)
        self.assertNotIn("Cancel".encode(), response.data)

    @requests_mock.mock()
    def test_sign_out_help_something_else(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        form = {"option": "something-else"}
        response = self.app.post("/help", data=form, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Further help".encode(), response.data)
        self.assertIn("You can find help for common issues if you".encode(), response.data)
        self.assertIn("If you are having problems signing in, please".encode(), response.data)
