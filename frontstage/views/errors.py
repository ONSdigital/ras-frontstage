import logging

from flask import Blueprint, make_response, render_template
from structlog import wrap_logger


logger = wrap_logger(logging.getLogger(__name__))

error_bp = Blueprint('error_bp', __name__, template_folder='templates/errors')


@error_bp.route('/', methods=['GET', 'POST'])
def default_error_page():
    response = make_response(render_template('errors/error.html', _theme='default', data={"error": {"type": "failed"}}))
    response.set_cookie('authorization', value='', expires=0)
    return response
