import logging

from flask import Blueprint, render_template
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))

contact_us_bp = Blueprint('contact_us_bp', __name__, static_folder='static', template_folder='templates')


# ===== Cookies Policy =====
@contact_us_bp.route('/', methods=['GET', 'POST'])
def contact_us():
    return render_template('contact-us.html', _theme='default')
