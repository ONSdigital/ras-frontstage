from uuid import uuid4

from frontstage import redis, jwt
from datetime import datetime, timedelta


class Session(object):

    def __init__(self, session_key, encoded_jwt_token):
        self.encoded_jwt_token = encoded_jwt_token
        self.session_key = session_key

    @classmethod
    def from_session_key(cls, session_key):
        encoded_jwt_token = redis.get(session_key)
        return cls(session_key, encoded_jwt_token)

    @classmethod
    def from_party_id(cls, party_id):
        """Create a new and unpersisted session object from a party_id, this will encode a JWT
            and set and expiry time, it will default the unread message count to 0
            you must persist this yourself by calling session.save()"""
        data_dict = {
            'party_id': party_id,
            "role": "respondent",
            'unread_message_count': {
                'value': 0,
                'refresh_in': _get_new_timestamp(300)
            }, 'expires_in': _get_new_timestamp(3600)}
        encoded_jwt_token = jwt.encode(data_dict)
        session_key = str(uuid4())
        session = cls(session_key, encoded_jwt_token)
        return session

    def update_session(self):
        decoded_jwt = self.get_decoded_jwt()
        decoded_jwt = _get_new_timestamp(decoded_jwt)
        self.encoded_jwt_token = jwt.encode(decoded_jwt)
        self.save()

    def delete_session(self, session_key):
        self.session_key = session_key
        redis.delete(self.session_key)

    def set_unread_message_total(self, total):
        decoded_token = self.get_decoded_jwt()
        decoded_token['unread_message_count']['value'] = total
        decoded_token['unread_message_count']['refresh_in'] = _get_new_timestamp(300)
        self.encoded_jwt_token = jwt.encode(decoded_token)
        self.save()

    def get_unread_message_count(self):
        return self.get_decoded_jwt()['unread_message_count']['value']

    def message_count_expired(self):
        return self.get_decoded_jwt()['unread_message_count']['refresh_in'] < datetime.now().timestamp()

    def get_encoded_jwt(self):
        return self.encoded_jwt_token

    def get_decoded_jwt(self):
        return jwt.decode(self.encoded_jwt_token)

    def save(self):
        redis.setex(self.session_key, 3600, self.encoded_jwt_token)


def _get_new_timestamp(ttl, time_func=lambda: datetime.now()):
    current_time = time_func()
    expires_in = current_time + timedelta(seconds=ttl)
    return expires_in.timestamp()
