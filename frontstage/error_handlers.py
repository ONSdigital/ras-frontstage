import logging
from os import getenv

from flask import redirect, url_for
from requests.exceptions import ConnectionError
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import ApiError, ExternalServiceError, JWTValidationError


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


@app.errorhandler(ApiError)
def api_error(error):
    logger.error('Api failed to retrieve required data', url=error.url, status_code=str(error.status_code))
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
