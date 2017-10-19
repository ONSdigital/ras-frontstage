from uuid import uuid4

from frontstage import redis


class SessionHandler(object):

    def __init__(self):
        self.session_key = None
        self.encoded_jwt = None

    def create_session(self, encoded_jwt):
        self.encoded_jwt = encoded_jwt
        self.session_key = self._create_key()
        redis.setex(self.session_key, 3600, self.encoded_jwt)

    def update_session(self, session_key=None):
        if session_key:
            self.get_encoded_jwt(session_key)
        redis.setex(self.session_key, 3600, self.encoded_jwt)

    def delete_session(self, session_key):
        self.session_key = session_key
        redis.delete(self.session_key)

    def get_encoded_jwt(self, session_key):
        self.session_key = session_key
        self.encoded_jwt = redis.get(self.session_key)
        return self.encoded_jwt

    @staticmethod
    def _create_key():
        return str(uuid4())
