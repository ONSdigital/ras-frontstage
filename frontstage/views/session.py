from flask import Blueprint, jsonify, make_response, redirect, request, session, url_for

from frontstage.common.authorisation import jwt_authorization
from frontstage.common.session import Session

session_bp = Blueprint("session", __name__)


@session_bp.route("/expires-at", methods=["GET"])
@jwt_authorization(request, refresh_session=False)
def session_expires_at(expires_at):
    return jsonify(expires_at=expires_at.get_formatted_expires_in())


@session_bp.route("/expires-at", methods=["PATCH"])
@jwt_authorization(request)
def session_refresh_expires_at(expires_at):
    return jsonify(expires_at=expires_at.get_formatted_expires_in())
