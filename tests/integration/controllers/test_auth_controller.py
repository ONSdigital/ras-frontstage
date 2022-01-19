import unittest

import responses

from config import TestingConfig
from frontstage import app
from frontstage.controllers import auth_controller
from frontstage.exceptions.exceptions import ApiError
from tests.integration.mocked_services import url_auth_delete


class TestBannerController(unittest.TestCase):
    def setUp(self):
        app_config = TestingConfig()
        app.config.from_object(app_config)
        self.app = app.test_client()
        self.app_config = self.app.application.config

    def test_delete_user_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.DELETE, url_auth_delete, status=204, content_type="application/json")
            with app.app_context():
                actual = auth_controller.delete_account("example@example.com")
                self.assertEqual(204, actual.status_code)

    def test_delete_user_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.DELETE, url_auth_delete, status=400, content_type="application/json")
            with app.app_context():
                with self.assertRaises(ApiError):
                    auth_controller.delete_account("")
