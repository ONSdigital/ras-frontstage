import logging
from os import getenv

from flask import redirect, url_for, render_template, request
from requests.exceptions import ConnectionError
from structlog import wrap_logger
from werkzeug.exceptions import RequestEntityTooLarge

from frontstage import app
from frontstage.exceptions.exceptions import ExternalServiceError, JWTValidationError


logger = wrap_logger(logging.getLogger(__name__))


@app.errorhandler(404)
def connection_error_not_found(error):  # pylint: disable=unused-argument
    return redirect(url_for('error_bp.not_found_error_page',
                            _external=True,
                            _scheme=getenv('SCHEME', 'http')))


@app.errorhandler(500)
def connection_error_internal_server(error):  # pylint: disable=unused-argument
    return redirect(url_for('error_bp.server_error_page',
                            _external=True,
                            _scheme=getenv('SCHEME', 'http')))


@app.errorhandler(ConnectionError)
def connection_error(error):
    logger.error('Failed to connect to external service', url=error.request.url)
    return redirect(url_for('error_bp.server_error_page',
                            _external=True,
                            _scheme=getenv('SCHEME', 'http')))


@app.errorhandler(ExternalServiceError)
def connection_error_external_service(error):
    logger.error('Error in external service', status_code=error.status_code, url=error.url)
    return redirect(url_for('error_bp.server_error_page',
                            _external=True,
                            _scheme=getenv('SCHEME', 'http')))


@app.errorhandler(JWTValidationError)
def connection_error_jwt_validation(error):  # pylint: disable=unused-argument
    return redirect(url_for('error_bp.not_logged_in_error_page',
                            _external=True,
                            _scheme=getenv('SCHEME', 'http')))


@app.errorhandler(RequestEntityTooLarge)
def request_entity_too_large_error(error):
    case_id = request.args.get('case_id', None)
    logger.error('Request Entity too large')
    error_info = 'size'

    return redirect(url_for('surveys_bp.upload_failed',
                            _external=True,
                            _scheme=getenv('SCHEME', 'http'),
                            case_id=case_id,
                            error_info=error_info))
