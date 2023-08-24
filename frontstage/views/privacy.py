import logging

from flask import Blueprint
from structlog import wrap_logger

from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))

privacy_bp = Blueprint("privacy_bp", __name__, static_folder="static", template_folder="templates")


@privacy_bp.route("/", methods=["GET"])
def privacy():
    return render_template("privacy-and-data-protection.html")
