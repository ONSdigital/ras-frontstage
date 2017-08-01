import logging

from flask import Blueprint, make_response, render_template
from structlog import wrap_logger


logger = wrap_logger(logging.getLogger(__name__))

error_bp = Blueprint('error_bp', __name__)


@error_bp.route('/', methods=['GET', 'POST'])
def error_page():
    response = make_response(render_template('error.html', _theme='default', data={"error": {"type": "failed"}}))
    response.set_cookie('authorization', value='', expires=0)
    return response
