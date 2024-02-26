import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import responses

from config import TestingConfig
from frontstage import app, jwt, redis
from frontstage.common.session import Session
from frontstage.controllers import conversation_controller
from frontstage.exceptions.exceptions import IncorrectAccountAccessError
from tests.integration.mocked_services import message_count, url_get_conversation_count


class TestConversationController(unittest.TestCase):
    def setUp(self):
        app_config = TestingConfig()
        app.config.from_object(app_config)
        self.app = app.test_client()
        self.app_config = self.app.application.config
        self.redis = redis
        self.redis.flushall()

    @patch("frontstage.controllers.conversation_controller._create_get_conversation_headers")
    def test_get_message_count_from_api(self, headers):
        headers.return_value = {"Authorization": "token"}
        session = Session.from_party_id("id")
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                url_get_conversation_count,
                json=message_count,
                status=200,
                headers={"Authorisation": "token"},
                content_type="application/json",
            )
            with app.app_context():
                count = conversation_controller.get_message_count_from_api(session)

                self.assertEqual(3, count)

    def test_get_message_count_from_session(self):
        session = Session.from_party_id("id")
        session.set_unread_message_total(3)
        with app.app_context():
            count = conversation_controller.try_message_count_from_session(session)

            self.assertEqual(3, count)

    def test_get_message_count_from_session_if_persisted_by_api(self):
        session = Session.from_party_id("id")
        session.set_unread_message_total(1)

        session_key = session.session_key

        session_under_test = Session.from_session_key(session_key)
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                url_get_conversation_count,
                json=message_count,
                status=200,
                headers={"Authorisation": "token"},
                content_type="application/json",
            )
            with app.app_context():
                count = conversation_controller.get_message_count_from_api(session_under_test)

                self.assertEqual(3, session_under_test.get_unread_message_count())
                self.assertEqual(3, count)

    @patch("frontstage.controllers.conversation_controller._create_get_conversation_headers")
    def test_get_message_count_from_api_when_expired(self, headers):
        headers.return_value = {"Authorization": "token"}
        session = Session.from_party_id("id")
        decoded = session.get_decoded_jwt()
        decoded["unread_message_count"]["refresh_in"] = (
            datetime.fromtimestamp(decoded["unread_message_count"]["refresh_in"]) - timedelta(seconds=301)
        ).timestamp()
        encoded = jwt.encode(decoded)
        session.encoded_jwt_token = encoded
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                url_get_conversation_count,
                json=message_count,
                status=200,
                headers={"Authorisation": "token"},
                content_type="application/json",
            )
            with app.app_context():
                count = conversation_controller.try_message_count_from_session(session)

                self.assertEqual(3, count)

    @patch("frontstage.controllers.conversation_controller._create_get_conversation_headers")
    def test_get_message_count_unauthorized(self, headers):
        headers.return_value = {"Authorization": "token"}
        session = Session.from_party_id("id")
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_conversation_count, status=403)
            with app.app_context():
                with self.assertRaises(IncorrectAccountAccessError):
                    conversation_controller.get_message_count_from_api(session)

    @patch("frontstage.controllers.conversation_controller._create_get_conversation_headers")
    def test_get_message_count_other_error_returns_0(self, headers):
        headers.return_value = {"Authorization": "token"}
        session = Session.from_party_id("id")
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_conversation_count, status=400)
            with app.app_context():
                count = conversation_controller.get_message_count_from_api(session)

                self.assertEqual(0, count)
