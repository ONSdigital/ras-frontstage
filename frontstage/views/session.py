from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from frontstage.common.authorisation import jwt_authorization

session_bp = Blueprint("session", __name__)


@session_bp.route("/expires-at", methods=["GET"])
@jwt_authorization(request, refresh_session=False)
def session_expires_at(session):
    expires_at = session.get_expires_in()
    return jsonify(expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc).isoformat())
