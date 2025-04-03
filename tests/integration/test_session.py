import unittest
from datetime import datetime, timedelta

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
        test_jwt = session.get_decoded_jwt()
        self.assertEqual(test_jwt["party_id"], "party")

    @freeze_time(TIME_TO_FREEZE)
    def test_refresh_session(self):
        # Create session and get session key
        session = Session.from_party_id("party")
        session.set()

        future_time = TIME_TO_FREEZE + timedelta(minutes=5)
        with freeze_time(future_time):
            session.refresh_session()

        # Check that the session expiry time has been extended
        expires_in = datetime.fromtimestamp(session.get_expires_in())

        self.assertEqual(expires_in, future_time + timedelta(minutes=60))

    def test_delete_session(self):
        # Create session and get session key
        session = Session.from_party_id("party")
        session.set()
        session_key = session.session_key
        session.delete_session()

        session = redis.get(session_key)

        self.assertEqual(session, None)

    def test_from_session_key(self):
        session = Session.from_party_id("party")
        session.set()
        session_key = session.session_key

        session_from_redis = Session.from_session_key(session_key)

        self.assertTrue(session_from_redis is not None)

        decoded_jwt = session_from_redis.get_decoded_jwt()
        self.assertEqual(decoded_jwt["party_id"], "party")
        self.assertEqual(session_from_redis.get_party_id(), "party")
