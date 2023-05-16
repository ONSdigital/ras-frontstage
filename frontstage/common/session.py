from datetime import datetime, timedelta, timezone
from uuid import uuid4

from frontstage import jwt, redis


class Session(object):
    def __init__(self, session_key, encoded_jwt_token):
        self.encoded_jwt_token = encoded_jwt_token
        self.session_key = session_key
        self.persisted = False

    @classmethod
    def from_session_key(cls, session_key):
        # Redis client throws an error if you try to .get(None)
        if session_key is None:
            encoded_jwt_token = None
        else:
            encoded_jwt_token = redis.get(session_key)
        session = cls(session_key, encoded_jwt_token)
        session.persisted = True
        return session

    @classmethod
    def from_party_id(cls, party_id):
        """Create a new and unpersisted session object from a party_id, this will encode a JWT
        and set an expiry time, it will default the unread message count to 0"""
        data_dict = {
            "party_id": party_id,
            "role": "respondent",
            "unread_message_count": {"value": 0, "refresh_in": _get_new_timestamp(ttl=300)},
            "expires_in": _get_new_timestamp(),
        }
        encoded_jwt_token = jwt.encode(data_dict)
        session_key = str(uuid4())
        session = cls(session_key, encoded_jwt_token)
        return session

    def refresh_session(self):
        """Refresh a session by setting a new expiry timestamp"""
        decoded_jwt = self.get_decoded_jwt()
        decoded_jwt["expires_in"] = _get_new_timestamp()
        self.encoded_jwt_token = jwt.encode(decoded_jwt)
        self.save()

    def delete_session(self):
        # Redis client throws an error if you try to .delete(None)
        if self.session_key:
            redis.delete(self.session_key)

    def set_unread_message_total(self, total):
        decoded_token = self.get_decoded_jwt()
        decoded_token["unread_message_count"]["value"] = total
        decoded_token["unread_message_count"]["refresh_in"] = _get_new_timestamp(ttl=300)
        self.encoded_jwt_token = jwt.encode(decoded_token)
        self.save()

    def get_unread_message_count(self):
        return self.get_decoded_jwt()["unread_message_count"]["value"]

    def message_count_expired(self):
        return self.get_decoded_jwt()["unread_message_count"]["refresh_in"] < datetime.now().timestamp()

    def get_party_id(self):
        return self.get_decoded_jwt()["party_id"]

    def get_encoded_jwt(self):
        return self.encoded_jwt_token

    def get_decoded_jwt(self):
        return jwt.decode(self.encoded_jwt_token)

    def get_expires_in(self):
        return jwt.decode(self.encoded_jwt_token)["expires_in"]

    def is_persisted(self):
        return self.persisted

    def save(self):
        redis.setex(self.session_key, 3600, self.encoded_jwt_token)
        self.persisted = True

    def get_formatted_expires_in(self, refresh=None):
        if refresh:
            self.refresh_session()
        return datetime.fromtimestamp(self.get_expires_in(), tz=timezone.utc).isoformat()


def _get_new_timestamp(ttl=3600):
    current_time = datetime.now()
    expires_in = current_time + timedelta(seconds=ttl)
    return expires_in.timestamp()
