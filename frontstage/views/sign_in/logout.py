import logging

from flask import make_response, redirect, request, url_for, flash
from structlog import wrap_logger

from frontstage.common.session import Session
from frontstage.views.sign_in import sign_in_bp

logger = wrap_logger(logging.getLogger(__name__))


@sign_in_bp.route('/logout')
def logout():
    # Delete user session in redis
    session_key = request.cookies.get('authorization')
    session = Session.from_session_key(session_key)
    session.delete_session()
    if request.args.get('csrf_error'):
        flash('To help protect your information we have signed you out.', 'info')
    # Delete session cookie
    response = make_response(redirect(url_for('sign_in_bp.login', next=request.args.get('next'))))
    response.set_cookie('authorization', value='', expires=0)
    return response
