import logging

from flask import Blueprint
from structlog import wrap_logger

from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))

contact_us_bp = Blueprint("contact_us_bp", __name__, static_folder="static", template_folder="templates")


@contact_us_bp.route("/", methods=["GET"])
def contact_us():
    return render_template("contact-us.html")
