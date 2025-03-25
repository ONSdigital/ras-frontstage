import unittest

import requests_mock

from frontstage import app
from tests.integration.mocked_services import url_banner_api


class TestSignOutHelp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie("authorization", "session_key")

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
