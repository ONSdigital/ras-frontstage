import json
import logging
from pathlib import Path

from flask import Blueprint, jsonify, make_response
from structlog import wrap_logger

from frontstage import talisman

logger = wrap_logger(logging.getLogger(__name__))

info_bp = Blueprint("info_bp", __name__, static_folder="static", template_folder="templates")

_health_check = {}
if Path("git_info").exists():
    with open("git_info") as io:
        _health_check = json.loads(io.read())


@info_bp.route("/", methods=["GET"])
@talisman(force_https=False)
def get_info():
    info = {
        "name": "ras-frontstage",
    }
    info = dict(_health_check, **info)

    return make_response(jsonify(info), 200)
