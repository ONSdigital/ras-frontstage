import unittest

import requests_mock

from frontstage import app
from tests.integration.mocked_services import url_banner_api


class TestCookiesContact(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    @requests_mock.mock()
    def test_cookies_success(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get("/cookies")

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Cookies on surveys.ons.gov.uk".encode() in response.data)
        self.assertTrue(
            "Cookies are small files saved on your phone, tablet or computer when you visit a website".encode()
            in response.data
        )

    @requests_mock.mock()
    def test_privacy_success(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get("/privacy-and-data-protection")

        self.assertEqual(response.status_code, 200)
        self.assertTrue("We will keep your information secure and confidential".encode() in response.data)
        self.assertTrue("Where can I find out more about how my information will be treated?".encode() in response.data)

    @requests_mock.mock()
    def test_contact_success(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get("/contact-us")

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Contact us".encode() in response.data)
        self.assertTrue('aria-label="Breadcrumbs"'.encode() in response.data)
        self.assertIn(b'href="mailto:surveys@ons.gov.uk"', response.data)
        self.assertIn(b'href="/sign-in/"', response.data)
