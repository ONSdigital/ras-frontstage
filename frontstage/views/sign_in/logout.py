import logging

from flask import make_response, redirect, request, url_for
from structlog import wrap_logger

from frontstage.common.session import SessionHandler
from frontstage.views.sign_in import sign_in_bp


logger = wrap_logger(logging.getLogger(__name__))


@sign_in_bp.route('/logout')
def logout():
    # Delete user session in redis
    session_key = request.cookies.get('authorization')
    session = SessionHandler()
    session.delete_session(session_key)

    # Delete session cookie
    response = make_response(redirect(url_for('sign_in_bp.login')))
    response.set_cookie('authorization', value='', expires=0)
    return response
