import unittest
from unittest.mock import patch

import responses

from config import TestingConfig
from frontstage import app, redis
from frontstage.controllers import conversation_controller
# from frontstage.exceptions.exceptions import IncorrectAccountAccessError
from tests.integration.mocked_services import url_get_conversation_count, message_count


class TestSurveyController(unittest.TestCase):

    def setUp(self):
        app_config = TestingConfig()
        app.config.from_object(app_config)
        self.app = app.test_client()
        self.app_config = self.app.application.config
        self.redis = redis
        self.redis.flushall()

    @patch("frontstage.controllers.conversation_controller._create_get_conversation_headers")
    @patch("frontstage.controllers.conversation_controller._set_unread_message_total")
    def test_get_message_count_from_api(self, headers, total):
        headers.return_value = "token"
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_conversation_count, json=message_count, status=200, headers={'Authorisation': 'token'}, content_type='application/json')
            with app.app_context():
                count = conversation_controller.get_message_count("party_id", from_session=False)

                self.assertEqual(3, count)

    @patch("frontstage.controllers.conversation_controller._create_get_conversation_headers")
    def test_get_message_count_unauthorized(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_conversation_count, json=message_count, status=200, headers={'Authorisation': 'token'}, content_type='application/json')
            with app.app_context():
                with self.assertRaises(IncorrectAccountAccessError):
                    conversation_controller.get_message_count("party_id", from_session=False)

    # def test_get_message_count_other_error_returns_0(self):
    #     with responses.RequestsMock() as rsps:
    #         rsps.add(rsps.GET, url_get_conversation_count, status=400)
    #         with app.app_context():
    #             count = conversation_controller.get_message_count("party_id", from_session=False)

    #             self.assertEqual(0, count)
