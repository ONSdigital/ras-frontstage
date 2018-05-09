import json
import unittest

from frontstage import app


class TestInfo(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        with open('git_info', 'w') as outfile:
            outfile.write(json.dumps({'test': 'test'}))

    def test_info_with_git_info(self):
        response = self.app.get("/info")

        self.assertEqual(response.status_code, 200)
        self.assertIn('"name": "ras-frontstage"'.encode(), response.data)
        self.assertIn('"test": "test"'.encode(), response.data)

    def test_strict_transport_security_header_is_set(self):
        response = self.app.get("/info", base_url='https://localhost')

        self.assertEqual(response.headers['Strict-Transport-Security'], 'max-age=31536000; includeSubDomains')

    def test_content_security_policy_header_is_set(self):
        response = self.app.get("/info")

        self.assertIn('font-src \'self\' data: https://cdn.ons.gov.uk https://fonts.gstatic.com https://maxcdn.bootstrapcdn.com', response.headers['Content-Security-Policy'])
        self.assertIn('default-src \'self\' https://cdn.ons.gov.uk', response.headers['Content-Security-Policy'])
        self.assertIn('connect-src \'self\' https://www.google-analytics.com https://cdn.ons.gov.uk', response.headers['Content-Security-Policy'])
        self.assertIn('img-src \'self\' data: https://www.google-analytics.com https://cdn.ons.gov.uk', response.headers['Content-Security-Policy'])
        self.assertIn('script-src \'self\' https://www.google-analytics.com https://cdn.ons.gov.uk https://code.jquery.com', response.headers['Content-Security-Policy'])
        self.assertIn('style-src \'self\' https://maxcdn.bootstrapcdn.com', response.headers['Content-Security-Policy'])

    def test_x_xss_protection_header_is_set(self):
        response = self.app.get("/info")

        self.assertEqual(response.headers['X-XSS-Protection'], '1; mode=block')

    def test_x_content_type_options_header_is_set(self):
        response = self.app.get("/info")

        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')

    def test_referrer_policy_header_is_set(self):
        response = self.app.get("/info")

        self.assertEqual(response.headers['Referrer-Policy'], 'same-origin')

    def test_x_frame_options_is_set(self):
        response = self.app.get("/info")

        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')
