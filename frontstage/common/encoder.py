import logging

from itsdangerous import URLSafeTimedSerializer
from structlog import wrap_logger

from frontstage import app


logger = wrap_logger(logging.getLogger(__name__))


class Encoder:

    def __init__(self):
        self.secret_key = app.config["SECRET_KEY"]
        self.email_token_salt = app.config["EMAIL_TOKEN_SALT"]

    def party_encode(self, email):
        timed_serializer = URLSafeTimedSerializer(self.secret_key)
        logger.debug('Encoded email address for party service')
        return timed_serializer.dumps(email, salt=self.email_token_salt)
