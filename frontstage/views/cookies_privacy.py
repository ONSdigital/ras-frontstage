import logging

from flask import Blueprint, render_template
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))

cookies_privacy_bp = Blueprint('cookies_privacy_bp', __name__, static_folder='static', template_folder='templates')


# ===== Cookies Policy =====
@cookies_privacy_bp.route('/', methods=['GET', 'POST'])
def cookies_privacy():
    return render_template('cookies-privacy.html', _theme='default')
