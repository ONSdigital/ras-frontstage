import logging
from datetime import datetime
from functools import wraps

from flask import url_for, flash
from jose import JWTError
from jose.jwt import decode
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage import app
from frontstage.common.session import Session
from frontstage.exceptions.exceptions import JWTValidationError


logger = wrap_logger(logging.getLogger(__name__))


def validate(token):
    logger.debug('Validating token')

    now = datetime.now().timestamp()
    expires_at = token.get('expires_at')
    if expires_at:
        if now >= expires_at:
            flash('To help protect your information we have signed you out.', 'info')
            logger.warning('Token has expired', expires_at=expires_at)
            return False
    else:
        logger.warning('No expiration date in token')
        return False

    logger.debug('Token is valid')
    return True


def jwt_authorization(request):
    jwt_secret = app.config['JWT_SECRET']

    def extract_session(original_function):
        @wraps(original_function)
        def extract_session_wrapper(*args, **kwargs):
            session_key = request.cookies.get('authorization')
            session = Session.from_session_key(session_key)
            encoded_jwt = session.get_encoded_jwt()
            if encoded_jwt:
                logger.debug('Attempting to authorize token')
                try:
                    jwt = decode(encoded_jwt, jwt_secret, algorithms='HS256')
                    logger.debug('Token decoded successfully')
                except JWTError:
                    logger.warning('Unable to decode token')
                    raise JWTValidationError
            else:
                logger.warning('No authorization token provided')
                flash('To help protect your information we have signed you out.', 'info')
                return redirect(url_for('sign_in_bp.login', next=request.url))

            if app.config['VALIDATE_JWT']:
                if validate(jwt):
                    session.refresh_session()
                    return original_function(session, *args, **kwargs)
                else:
                    logger.warning('Token is not valid for this request')
                    raise JWTValidationError
        return extract_session_wrapper
    return extract_session
