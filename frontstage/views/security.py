import logging

from flask import Blueprint, send_from_directory
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))

security_bp = Blueprint("security_bp", __name__, static_folder="static", template_folder="templates")


@security_bp.route("/<path:filename>", methods=["GET"])
def download_file(filename):
    return send_from_directory("static/.well-known/", filename)
