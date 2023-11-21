import logging

from flask import Blueprint
from structlog import wrap_logger

from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))

cookies_bp = Blueprint("cookies_bp", __name__, static_folder="static", template_folder="templates")


@cookies_bp.route("/", methods=["GET"])
def cookies():
    return render_template("cookies.html")
