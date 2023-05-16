from flask import Blueprint, jsonify, make_response, redirect, request, session, url_for

from frontstage.common.authorisation import jwt_authorization
from frontstage.common.session import Session

session_bp = Blueprint("session", __name__)


@session_bp.route("/expires-at", methods=["GET", "PATCH"])
@jwt_authorization(request, refresh_session=False)
def session_expires_at(expires_at):
    refresh = None
    if request.method == "PATCH":
        refresh = True
    return jsonify(expires_at=expires_at.get_formatted_expires_in(refresh))


@session_bp.route("/session-expired", methods=["GET"])
def session_expired():
    # Delete user session in redis
    session_key = request.cookies.get("authorization")
    current_session = Session.from_session_key(session_key)
    current_session.delete_session()
    # We need to remove the next value from the flask session otherwise, user is redirected to the expiry end point and
    # Not the survey list page
    if session.get("next"):
        session.pop("next")
    # Delete session cookie
    response = make_response(redirect(url_for("sign_in_bp.login")))
    response.delete_cookie("authorization")
    return response
