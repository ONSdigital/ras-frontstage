import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from freezegun import freeze_time

from frontstage import app, redis
from frontstage.common.session import Session

TIME_TO_FREEZE = datetime(2024, 1, 1, 12, 0, 0)


class TestSession(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.redis = redis
        self.redis.flushall()

    def test_create_session(self):
        # Create session and get session key
        session = Session.from_party_id("party")

        self.assertFalse(session.is_persisted())
        session.save()
        self.assertTrue(session.is_persisted())
        # Retrieve encoded_jwt from session
        test_jwt = session.get_decoded_jwt()
        self.assertEqual(test_jwt["party_id"], "party")
        self.assertEqual(test_jwt["unread_message_count"]["value"], 0)

    @freeze_time(TIME_TO_FREEZE)
    def test_refresh_session(self):
        # Create session and get session key
        session = Session.from_party_id("party")
        session.save()

        future_time = TIME_TO_FREEZE + timedelta(minutes=5)
        with freeze_time(future_time):
            session.refresh_session()

        # Check that the session expiry time has been extended
        expires_in = datetime.fromtimestamp(session.get_expires_in())

        self.assertEqual(expires_in, future_time + timedelta(minutes=60))

    def test_delete_session(self):
        # Create session and get session key
        session = Session.from_party_id("party")
        session.save()
        session_key = session.session_key
        session.delete_session()

        session = redis.get(session_key)

        self.assertEqual(session, None)

    def test_from_session_key(self):
        session = Session.from_party_id("party")
        session.save()
        session_key = session.session_key

        session_from_redis = Session.from_session_key(session_key)

        self.assertTrue(session_from_redis is not None)

        decoded_jwt = session_from_redis.get_decoded_jwt()
        self.assertEqual(decoded_jwt["party_id"], "party")
        self.assertEqual(session_from_redis.get_party_id(), "party")

    def test_unread_message_count(self):
        session = Session.from_party_id("party")
        session.save()

        self.assertFalse(session.message_count_expired())

        session.set_unread_message_total(5)

        key = session.session_key
        session_to_assert = Session.from_session_key(key)

        self.assertEqual(session_to_assert.get_unread_message_count(), 5)

    @patch("frontstage.common.session._get_new_timestamp")
    def test_message_count_expired(self, test_patch):
        expired_time = datetime.now() - timedelta(seconds=301)
        test_patch.return_value = expired_time.timestamp()
        session = Session.from_party_id("party")
        session.save()

        self.assertTrue(session.message_count_expired())
