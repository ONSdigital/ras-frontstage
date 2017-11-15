import unittest

from frontstage import app


class TestCookiesContact(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_cookies_success(self):
        response = self.app.get('/cookies-privacy')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Cookies and privacy'.encode() in response.data)
        self.assertTrue('Your privacy is very important to us'.encode() in response.data)

    def test_contact_success(self):
        response = self.app.get('/contact-us')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Contact us'.encode() in response.data)
        self.assertTrue('Opening hours:'.encode() in response.data)
