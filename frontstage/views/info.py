import logging

from flask import jsonify, Blueprint
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))

info_bp = Blueprint('info_bp', __name__, static_folder='static', template_folder='templates')


@info_bp.route('/', methods=['GET'])
def get_info():
    """Rest endpoint to provide application information"""
    details = {'name': 'secure_message',
               'version': '0.0.1',
               'origin': 'https://github.com/ONSdigital/ras-secure-message.git',
               'commit': 'not specified',
               'branch': 'not specified',
               'built': '01-01-1900 00:00:00.000'}

    return jsonify(details)
