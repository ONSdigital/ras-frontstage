import logging

import structlog
from flask import current_app
from itsdangerous import URLSafeTimedSerializer
from werkzeug.exceptions import InternalServerError


logger = structlog.wrap_logger(logging.getLogger(__name__))


def generate_email_token(email):
    """Creates a token based on a provided email address

    :param email: email address of the respondent
    :return: A serialised string containing the email address
    """
    secret_key = current_app.config["SECRET_KEY"]
    email_token_salt = current_app.config["EMAIL_TOKEN_SALT"]

    # TODO: eventually implement a service startup check for all required config values
    if secret_key is None or email_token_salt is None:
        msg = "SECRET_KEY or EMAIL_TOKEN_SALT are not configured."
        logger.error(msg)
        raise InternalServerError(msg)

    timed_serializer = URLSafeTimedSerializer(secret_key)
    return timed_serializer.dumps(email, salt=email_token_salt)


def decode_email_token(token, duration=None):
    """Decodes a token and returns the result

    :param token: A serialised string
    :param duration: The amount of time in seconds the token is valid for.  If the token is older
    then this number, an exception will be thrown. Default is None.
    :return: The contents of the deserialised token
    """
    logger.info('Decoding email verification token', token=token)

    timed_serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    email_token_salt = current_app.config["EMAIL_TOKEN_SALT"]

    result = timed_serializer.loads(token, salt=email_token_salt, max_age=duration)
    logger.info('Successfully decoded email verification token', token=token)
    return result
