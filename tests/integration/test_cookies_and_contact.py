import unittest

from frontstage import app


class TestCookiesContact(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_cookies_success(self):
        response = self.app.get('/cookies')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Cookies on ONS Business Surveys'.encode() in response.data)
        self.assertTrue('Cookies are small files saved on your phone, tablet or computer when you visit a website'.encode() in response.data)

    def test_privacy_success(self):
        response = self.app.get('/privacy-and-data-protection')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Privacy and data protection'.encode() in response.data)
        self.assertTrue('Your privacy is very important to us'.encode() in response.data)

    def test_contact_success(self):
        response = self.app.get('/contact-us')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Contact us'.encode() in response.data)
        self.assertTrue('Opening hours:'.encode() in response.data)
