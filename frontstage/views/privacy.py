import logging

from flask import Blueprint, render_template
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))

privacy_bp = Blueprint("privacy_bp", __name__, static_folder="static", template_folder="templates")


@privacy_bp.route("/", methods=["GET"])
def privacy():
    return render_template("privacy-and-data-protection.html")
