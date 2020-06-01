import time
import unittest

from datetime import datetime, timedelta
from frontstage import app, redis
from frontstage.common.session import Session, datetime_supplier


class TestSession(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.redis = redis
        self.redis.flushall()

    def test_create_session(self):
        # Create session and get session key
        session = Session.from_party_id("party")
        session.save()

        # Retrieve encoded_jwt from session
        test_jwt = session.get_decoded_jwt()
        self.assertEqual(test_jwt['party_id'], "party")
        self.assertEqual(test_jwt['unread_message_count']['value'], 0)

    def test_update_session(self):
        # Create session and get session key
        session = Session.from_party_id("party")
        session.save()
        session_key = session.session_key

        # Wait 3 seconds and update the session
        time.sleep(1)
        session.update_session()

        # Check that the session expiry time has been reset
        expires_in = redis.ttl(session_key)
        self.assertEqual(expires_in, 3600)

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

    def test_unread_message_count(self):
        session = Session.from_party_id("party")
        session.save()

        self.assertFalse(session.message_count_expired())

        session.set_unread_message_total(5)

        key = session.session_key
        session_to_assert = Session.from_session_key(key)

        self.assertEqual(session_to_assert.get_unread_message_count(), 5)

    def test_message_count_expired(self):
        datetime_supplier = lambda: datetime.now() - timedelta(seconds=301)
        session = Session.from_party_id("party")
        session.save()

        self.assertTrue(session.message_count_expired())
