import json
import logging
from pathlib import Path

from flask import Blueprint, jsonify, make_response
from structlog import wrap_logger

from frontstage import app


logger = wrap_logger(logging.getLogger(__name__))
info_bp = Blueprint('info_bp', __name__, static_folder='static', template_folder='templates')


@info_bp.route('/', methods=['GET'])
def get_info():
    info = {
        "name": 'ras-frontstage',
        "version": app.config['VERSION'],
        'status': 'OK',
    }

    return jsonify(info)
