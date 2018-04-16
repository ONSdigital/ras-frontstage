import unittest

from frontstage import app


class TestInfo(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_info_with_git_info(self):
        response = self.app.get("/info")

        self.assertEqual(response.status_code, 200)
        self.assertIn('"name": "ras-frontstage"'.encode(), response.data)
        self.assertIn('"test": "test"'.encode(), response.data)

    def test_strict_transport_security_header_is_set(self):
        with open('git_info', 'w') as outfile:
            outfile.write('"test": "test"')

        response = self.app.get("/info")

        self.assertEqual(response.headers['Strict-Transport-Security'], 'max-age=31536000; includeSubDomains')

    def test_content_security_policy_header_is_set(self):
        with open('git_info', 'w') as outfile:
            outfile.write('"test": "test"')

        response = self.app.get("/info")

        self.assertEqual(response.headers['Content-Security-Policy'], "default-src 'self'")

    def test_x_xss_protection_header_is_set(self):
        with open('git_info', 'w') as outfile:
            outfile.write('"test": "test"')

        response = self.app.get("/info")

        self.assertEqual(response.headers['X-XSS-Protection'], '1')

    def test_x_content_type_options_header_is_set(self):
        with open('git_info', 'w') as outfile:
            outfile.write('"test": "test"')

        response = self.app.get("/info")

        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')

    def test_referrer_policy_header_is_set(self):
        with open('git_info', 'w') as outfile:
            outfile.write('"test": "test"')

        response = self.app.get("/info")

        self.assertEqual(response.headers['Referrer-Policy'], 'same-origin')
