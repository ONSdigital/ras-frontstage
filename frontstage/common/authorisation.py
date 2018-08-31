import logging
from datetime import datetime
from functools import wraps

from jose import JWTError
from jose.jwt import decode
from structlog import wrap_logger

from frontstage import app
from frontstage.common.session import SessionHandler
from frontstage.exceptions.exceptions import JWTValidationError


logger = wrap_logger(logging.getLogger(__name__))


def validate(token):
    logger.debug('Validating token')

    now = datetime.now().timestamp()
    expires_at = token.get('expires_at')
    if expires_at:
        if now >= expires_at:
            logger.warning('Token has expired', expires_at=expires_at)
            return False
    else:
        logger.warning('No expiration date in token')
        return False

    logger.debug('Token is valid')
    return True


def jwt_authorization(request):
    jwt_secret = app.config['JWT_SECRET']
    jwt_algorithm = app.config['JWT_ALGORITHM']

    def extract_session(original_function):
        @wraps(original_function)
        def extract_session_wrapper(*args, **kwargs):
            session_handler = SessionHandler()
            session_key = request.cookies.get('authorization')
            encoded_jwt = session_handler.get_encoded_jwt(session_key)
            if encoded_jwt:
                logger.debug('Attempting to authorize token')
                try:
                    jwt = decode(encoded_jwt, jwt_secret, algorithms=jwt_algorithm)
                    logger.debug('Token decoded successfully')
                except JWTError:
                    logger.warning('Unable to decode token')
                    raise JWTValidationError
            else:
                logger.warning('No authorization token provided')
                raise JWTValidationError

            if app.config['VALIDATE_JWT']:
                if validate(jwt):
                    session_handler.update_session()
                    return original_function(jwt, *args, **kwargs)
                else:
                    logger.warning('Token is not valid for this request')
                    raise JWTValidationError
        return extract_session_wrapper
    return extract_session
