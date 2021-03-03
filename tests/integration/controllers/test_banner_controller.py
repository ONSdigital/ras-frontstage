import unittest

import responses

from config import TestingConfig
from frontstage import app
from frontstage.controllers import banner_controller
from tests.integration.mocked_services import url_banner_api


class TestBannerController(unittest.TestCase):

    def setUp(self):
        app_config = TestingConfig()
        app.config.from_object(app_config)
        self.app = app.test_client()
        self.app_config = self.app.application.config

    def test_get_case_by_id_success(self):
        response_json = {'id': 'active',
                         'content': 'This is a banner'}
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_banner_api, json=response_json, status=200, content_type='application/json')
            with app.app_context():
                expected = response_json['content']
                actual = banner_controller.current_banner()
                self.assertEqual(expected, actual)

    def test_get_banner_not_found(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_banner_api, status=404, content_type='application/json')
            with app.app_context():
                expected = ""
                actual = banner_controller.current_banner()
                self.assertEqual(expected, actual)

    def test_get_banner_server_error(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_banner_api, status=500, content_type='application/json')
            with app.app_context():
                expected = ""
                actual = banner_controller.current_banner()
                self.assertEqual(expected, actual)

    @responses.activate
    def test_get_banner_connection_error(self):
        """responses.activate will raise a ConnectionError if a url isn't mocked.  On a connection error
        we want to be sure that we'll still get an empty string response if it's not working
        """
        with app.app_context():
            with self.assertLogs(level='INFO') as logs:
                expected = ""
                actual = banner_controller.current_banner()
                self.assertEqual(expected, actual)
                self.assertIn("Failed to connect to banner", logs.output[0])
