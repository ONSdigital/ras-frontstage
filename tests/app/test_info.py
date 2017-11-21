import unittest

from frontstage import app


class TestInfo(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()

    def test_info_with_git_info(self):
        response = self.app.get("/info")

        self.assertEqual(response.status_code, 200)
        self.assertIn('"name": "ras-frontstage"'.encode(), response.data)
        self.assertIn('test'.encode(), response.data)
