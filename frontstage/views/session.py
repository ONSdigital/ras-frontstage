from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from frontstage.common.authorisation import jwt_authorization

session_bp = Blueprint("session", __name__)


@session_bp.route("/expires-at", methods=["GET", "PATCH"])
@jwt_authorization(request, refresh_session=False)
def session_expires_at(session):
    return jsonify(expires_at=datetime.fromtimestamp(session.get_expires_in(), tz=timezone.utc).isoformat())
