import unittest

from flask import abort

from frontstage import app
from frontstage.error_handlers import not_found_error


class TestErrorHandlers(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_not_found_error(self):
        response = abort(404)

        self.assertEqual(response.status_code, 404)
        # self.assertTrue('Server error'.encode() in response.data)