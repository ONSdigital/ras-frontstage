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


@error_bp.route('/404', methods=['GET', 'POST'])
def not_found_error_page():
    return render_template('errors/404-error.html', _theme='default', data={"error": {"type": "failed"}}), 404


@error_bp.route('/500', methods=['GET', 'POST'])
def server_error_page():
    return render_template('errors/500-error.html', _theme='default', data={"error": {"type": "failed"}}), 500


@error_bp.route('/403', methods=['GET', 'POST'])
def not_logged_in_error_page():
    return render_template('errors/not-signed-in.html', _theme='default', data={"error": {"type": "failed"}}), 403
