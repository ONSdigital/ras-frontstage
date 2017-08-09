import logging

from flask import redirect, url_for
from requests.exceptions import ConnectionError
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import ExternalServiceError


logger = wrap_logger(logging.getLogger(__name__))


@app.errorhandler(404)
def connection_error(error):
    return redirect(url_for('error_bp.not_found_error_page'))


@app.errorhandler(500)
def connection_error(error):
    return redirect(url_for('error_bp.server_error_page'))


@app.errorhandler(ConnectionError)
def connection_error(error):
    logger.error("Failed to connect to {}".format(error.request.url))
    return redirect(url_for('error_bp.server_error_page'))


@app.errorhandler(ExternalServiceError)
def connection_error(error):
    logger.error("Error in external service at: {} status code: {}".format(error.url, error.status_code))
    return redirect(url_for('error_bp.server_error_page'))

