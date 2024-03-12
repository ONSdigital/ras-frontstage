import logging
from datetime import datetime
from functools import wraps

from jwt import decode
from jwt.exceptions import DecodeError
from structlog import wrap_logger
from werkzeug.exceptions import Unauthorized

from frontstage import app
from frontstage.common.session import Session
from frontstage.exceptions.exceptions import JWTTimeoutError, JWTValidationError

logger = wrap_logger(logging.getLogger(__name__))

EXPIRES_IN_MISSING_FROM_PAYLOAD = "The decoded JWT payload doesn't contain the key expires_in"
NO_AUTHORIZATION_COOKIE = "The respondent doesn't have an authorization cookie"
NO_ENCODED_JWT = "The session key doesn't return an encoded JWT"
JWT_DATE_EXPIRED = "The JWT has expired for party_id"
JWT_DECODE_ERROR = "The encoded JWT could not be decoded for session key"


def jwt_authorization(request, refresh_session=True):
    def extract_session(original_function):
        @wraps(original_function)
        def extract_session_wrapper(*args, **kwargs):
            if not (session_key := request.cookies.get("authorization")):
                raise Unauthorized(NO_AUTHORIZATION_COOKIE)

            redis_session = Session.from_session_key(session_key)
            encoded_jwt = redis_session.get_encoded_jwt()

            if not encoded_jwt:
                raise Unauthorized(NO_ENCODED_JWT)

            try:
                jwt = decode(encoded_jwt, app.config["JWT_SECRET"], algorithms="HS256")
            except DecodeError:
                raise JWTValidationError(f"{JWT_DECODE_ERROR} {session_key}")

            _validate_jwt_date(jwt)

            if refresh_session:
                redis_session.refresh_session()

            return original_function(redis_session, *args, **kwargs)

        return extract_session_wrapper

    return extract_session


def _validate_jwt_date(token):
    if expires_in := token.get("expires_in"):
        if datetime.now().timestamp() <= expires_in:
            return

        raise JWTTimeoutError(f"{JWT_DATE_EXPIRED} {token.get('party_id')}")

    raise JWTValidationError(f"{EXPIRES_IN_MISSING_FROM_PAYLOAD} {token.get('party_id')}")
