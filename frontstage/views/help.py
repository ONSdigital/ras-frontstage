import logging

from flask import Blueprint, render_template
from structlog import wrap_logger


logger = wrap_logger(logging.getLogger(__name__))

help_bp = Blueprint('help_bp', __name__,
                          static_folder='static', template_folder='templates')


@help_bp.route('/vulnerability-reporting', methods=['GET'])
def help():
    return render_template('vunerability_disclosure.html')