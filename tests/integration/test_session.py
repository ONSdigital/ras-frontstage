import time
import unittest

from frontstage import app, redis
from frontstage.common.session import SessionHandler


class TestSession(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.redis = redis
        self.redis.flushall()

    def test_create_session(self):
        # Create session and get session key
        session = SessionHandler()
        session.create_session(encoded_jwt='test_jwt')
        session_key = session.session_key

        # Retrieve encoded_jwt from session
        test_jwt = self.redis.get(session_key)
        self.assertEqual(test_jwt, 'test_jwt'.encode())

    def test_update_session(self):
        # Create session and get session key
        session = SessionHandler()
        session.create_session(encoded_jwt='test_jwt')
        session_key = session.session_key

        # Wait 3 seconds and update the session
        time.sleep(3)
        session.update_session()

        # Check that the session expiry time has been reset
        expires_in = redis.ttl(session_key)
        self.assertEqual(expires_in, 3600)

    def test_update_session_with_session_key(self):
        # Create session and get session key
        session = SessionHandler()
        session.create_session(encoded_jwt='test_jwt')
        session_key = session.session_key

        # Wait 3 seconds and update the session
        time.sleep(3)
        session.update_session(session_key)

        # Check that the session expiry time has been reset
        expires_in = redis.ttl(session_key)
        self.assertEqual(expires_in, 3600)

    def test_get_encoded_jwt(self):
        # Create session and get session key
        session = SessionHandler()
        session.create_session(encoded_jwt='test_jwt')
        session_key = session.session_key

        encoded_jwt = session.get_encoded_jwt(session_key)

        self.assertEqual(encoded_jwt, 'test_jwt'.encode())

    def test_delete_session(self):
        # Create session and get session key
        session = SessionHandler()
        session.create_session(encoded_jwt='test_jwt')
        session_key = session.session_key
        session.delete_session(session_key)

        session = redis.get(session_key)

        self.assertEqual(session, None)
