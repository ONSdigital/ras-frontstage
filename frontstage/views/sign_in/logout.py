import logging

from flask import flash, get_flashed_messages, make_response, redirect, request, url_for
from structlog import wrap_logger

from frontstage.common.session import Session
from frontstage.views.sign_in import sign_in_bp

logger = wrap_logger(logging.getLogger(__name__))

SIGN_OUT_GUIDANCE = "To help protect your information we have signed you out."


@sign_in_bp.route("/logout")
def logout():
    flashed_messages = get_flashed_messages(with_categories=True)
    # Delete user session in redis
    session_key = request.cookies.get("authorization")
    session = Session.from_session_key(session_key)
    session.delete_session()
    if len(flashed_messages) > 0:
        for category, message in flashed_messages:
            flash(message=message, category=category)
    if request.args.get("sign_out_guidance"):
        flash(SIGN_OUT_GUIDANCE, "info")
    # Delete session cookie
    response = make_response(redirect(url_for("sign_in_bp.login", next=request.args.get("next"))))
    response.delete_cookie("authorization")
    return response
