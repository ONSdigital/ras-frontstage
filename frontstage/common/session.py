from uuid import uuid4

from frontstage import redis


class SessionHandler(object):

    def __init__(self):
        self.session_key = None
        # Currently the encoded_jwt is synonymous wth the session
        self.encoded_jwt = None

    def create_session(self, encoded_jwt):
        self.encoded_jwt = encoded_jwt
        self.session_key = 'session: {}'.format(self._create_key())
        redis.setex(self.session_key, 3600, encoded_jwt)

    def get_encoded_jwt(self, session_key):
        self.session_key = session_key
        self.encoded_jwt = redis.get(self.session_key)
        return self.encoded_jwt

    @staticmethod
    def _create_key():
        return str(uuid4())
