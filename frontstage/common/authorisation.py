from datetime import datetime
from functools import wraps
from flask import render_template
from jose import JWTError
from jose.jwt import decode

from frontstage import app


def jwt_authorization(request):
    """
    Validate an incoming session and only proceed with a decoded session if the session is valid,
    otherwise render the not-logged-in page.
    :param request: The current request object
    """

    jwt_secret = 'vrwgLNWEffe45thh545yuby'
    jwt_algorithm = 'HS256'

    def extract_session(original_function):
        @wraps(original_function)
        def extract_session_wrapper(*args, **kwargs):
            if 'authorization' in request.cookies:
                jwt_token = decode(request.cookies['authorization'], jwt_secret, algorithms=jwt_algorithm)
            else:
                return render_template('not-signed-in.html', _theme='default', data={"error": {"type": "failed"}})
            if app.config['VALIDATE_JWT']:
                valid = validate(jwt_token)
            if valid:
                return original_function(session, *args, **kwargs)
            else:
                return render_template('not-signed-in.html', _theme='default', data={"error": {"type": "failed"}}), 403
        return extract_session_wrapper
    return extract_session


def validate(jwt_token):
    """
    This function checks a jwt token for a required scope type.
    :param scope: The scopes to test against
    :param jwt_token: The incoming request object
    :return: Token is value, True or False
    """
    # logger.debug('event="validating token", token="{}", scope="{}"'.format(jwt_token, scope))
    try:
        token = decode(jwt_token)
    except JWTError:
        logger.warning('event="unable to decode token", token="{}"'.format(jwt_token))
        return False

    now = datetime.now().timestamp()
    if now >= token.get('expires_at', now):
        logger.warning('event="token has expired", token="{}"'.format(token))
        return False

    if not set(scope).intersection(token.get('scope', [])):
        logger.warning('event="unable to validate scope", token="{}"'.format(token))
        return False

    return True


def validate_jwt(scope, request, logger):
    """
    Validate the incoming JWT token, don't allow access to the endpoint unless we pass this test

    :param scope: A list of scope identifiers used to protect the endpoint
    :param request: The incoming request object
    :return: Exit variables from the protected function
    """
    def authorization_required_decorator(original_function):
        @wraps(original_function)
        def authorization_required_wrapper(*args, **kwargs):
            if not app.config['VALIDATE_JWT']:
                return original_function(*args, **kwargs)
            if validate(scope, request.headers.get('authorization', '')):
                return original_function(*args, **kwargs)
            return "Access forbidden", 403
        return authorization_required_wrapper
    return authorization_required_decorator


def validate(scope, jwt_token, logger):
    """
    This function checks a jwt token for a required scope type.
    :param scope: The scopes to test against
    :param jwt_token: The incoming request object
    :return: Token is value, True or False
    """
    logger.debug('event="validating token", token="{}", scope="{}"'.format(jwt_token, scope))
    try:
        token = decode(jwt_token)
    except JWTError:
        logger.warning('event="unable to decode token", token="{}"'.format(jwt_token))
        return False

    now = datetime.now().timestamp()
    if now >= token.get('expires_at', now):
        logger.warning('event="token has expired", token="{}"'.format(token))
        return False

    if not set(scope).intersection(token.get('scope', [])):
        logger.warning('event="unable to validate scope", token="{}"'.format(token))
        return False

    return True
