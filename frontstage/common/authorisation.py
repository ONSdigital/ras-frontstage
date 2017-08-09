from functools import wraps
from flask import render_template
from jose.jwt import encode, decode

def jwt_authorisation(request):
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
                session = decode(request.cookies['authorization'], jwt_secret, algorithms=jwt_algorithm)
            else:
                session = None
            if not session:
                return render_template('not-signed-in.html', _theme='default', data={"error": {"type": "failed"}})
            return original_function(session)
        return extract_session_wrapper
    return extract_session