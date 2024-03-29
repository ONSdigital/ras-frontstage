import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from freezegun import freeze_time

from frontstage import app
from frontstage.common.session import Session

SESSION_TIMEOUT_SECONDS = 3600
SESSION_KEY = "d06ce641-ab91-4f30-a78a-2098f8297768"
TIME_TO_FREEZE = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
PARTY_ID = "f49e945d-f992-49ac-ab7f-3c0fb953775e"


class TestSession(unittest.TestCase):
    @freeze_time(TIME_TO_FREEZE)
    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie(domain="localhost", key="authorization", value=SESSION_KEY)
        session = Session.from_party_id(PARTY_ID)
        self.encoded_jwt_token = session.encoded_jwt_token

    @freeze_time(TIME_TO_FREEZE)
    @patch("redis.StrictRedis.get")
    def test_expires_at_current_time(self, mock_redis):
        # Given a user has a valid jwt_token set to expire in 60 minutes
        mock_redis.return_value = self.encoded_jwt_token
        # When the expires-at end point is called
        with freeze_time(TIME_TO_FREEZE):
            response = self.app.get("/session/expires-at")
            expected_expires_at = (TIME_TO_FREEZE + timedelta(seconds=SESSION_TIMEOUT_SECONDS)).isoformat()
            parsed_json = json.loads(response.data)

        # Then the expiration time is in 60 minutes
        self.assertEqual(expected_expires_at, parsed_json["expires_at"])
        self.assertEqual((TIME_TO_FREEZE + timedelta(minutes=60)).isoformat(), expected_expires_at)

    @freeze_time(TIME_TO_FREEZE)
    @patch("redis.StrictRedis.get")
    def test_expires_at_future_time(self, mock_redis):
        # Given a user has a valid jwt_token set to expire in 60 minutes
        mock_redis.return_value = self.encoded_jwt_token
        # When the expires-at end point is called 20 minutes after it was set
        future_time = TIME_TO_FREEZE + timedelta(minutes=20)
        with freeze_time(future_time):
            response = self.app.get("/session/expires-at")
            expected_expires_at = (TIME_TO_FREEZE + timedelta(seconds=SESSION_TIMEOUT_SECONDS)).isoformat()
            parsed_json = json.loads(response.data)

        # Then the expiration time is in 40 minutes as calling expires-at doesn't extend the session
        self.assertEqual(expected_expires_at, parsed_json["expires_at"])
        self.assertEqual((future_time + timedelta(minutes=40)).isoformat(), expected_expires_at)

    @freeze_time(TIME_TO_FREEZE)
    @patch("redis.StrictRedis.get")
    def test_expire_at_patch_extends_session(self, mock_redis):
        # Given a user has a valid jwt_token set to expire in 60 minutes
        mock_redis.return_value = self.encoded_jwt_token
        # When the expires-at end point is patched we receive an updated expires-at value
        request_time = TIME_TO_FREEZE + timedelta(minutes=20)
        with freeze_time(request_time):
            response = self.app.patch("/session/expires-at")
            parsed_json = json.loads(response.data)
            expected_expires_at = (request_time + timedelta(seconds=SESSION_TIMEOUT_SECONDS)).isoformat()

        # Then the expires value is 60 minutes greater than it was
        self.assertEqual(parsed_json["expires_at"], expected_expires_at)
