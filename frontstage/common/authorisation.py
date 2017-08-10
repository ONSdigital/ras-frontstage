import logging

from datetime import datetime
from functools import wraps
from flask import render_template
from jose import JWTError
from jose.jwt import decode
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import JWTValidationError


logger = wrap_logger(logging.getLogger(__name__))


def validate(token):
    logger.debug('event="Validating token"')

    now = datetime.now().timestamp()
    expires_at = token.get('expires_at')
    if expires_at:
        if now >= expires_at:
            logger.warning('event="Token has expired", expires_at='.format(token))
            return False
    else:
        logger.warning('event="No expiration date in token"')
        return False

    # if not set('respondent').intersection(token.get('scope', [])):
    #     # logger.warning('event="unable to validate scope", token="{}"'.format(token))
    #     return False

    logger.debug('event="Token is valid"')
    return True


def jwt_authorization(request):

    jwt_secret = 'vrwgLNWEffe45thh545yuby'
    jwt_algorithm = 'HS256'

    def extract_session(original_function):
        @wraps(original_function)
        def extract_session_wrapper(*args, **kwargs):
            encrypted_jwt_token = request.cookies.get('authorization')
            if encrypted_jwt_token:
                logger.debug('event="Attempting to authorize token", "{}"'.format(encrypted_jwt_token))
                try:
                    jwt_token = decode(request.cookies['authorization'], jwt_secret, algorithms=jwt_algorithm)
                    logger.debug('event="Token decoded successfully"')
                except JWTError:
                    logger.warning('event="Unable to decode token", encrypted_jwt_token="{}"'
                                   .format(encrypted_jwt_token))
                    raise JWTValidationError
            else:
                logger.warning('event="No authorization token provided"')
                raise JWTValidationError

            if app.config['VALIDATE_JWT']:
                valid = validate(jwt_token)
            if valid:
                return original_function(jwt_token, *args, **kwargs)
            else:
                logger.warning('event="Token is not valid for this request"')
                raise JWTValidationError
        return extract_session_wrapper
    return extract_session
