from flask import Blueprint, jsonify, request

from frontstage.common.authorisation import jwt_authorization

session_bp = Blueprint("session", __name__)


@session_bp.route("/expires-at", methods=["GET"])
@jwt_authorization(request, refresh_session=False)
def session_expires_at(expires_at):
    return jsonify(expires_at=expires_at.get_formatted_expires_in())


@session_bp.route("/expires-at", methods=["PATCH"])
@jwt_authorization(request)
def session_refresh_expires_at(expires_at):
    return jsonify(expires_at=expires_at.get_formatted_expires_in())
