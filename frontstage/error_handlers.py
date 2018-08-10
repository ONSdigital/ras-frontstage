import logging

from flask import render_template, request
from requests.exceptions import ConnectionError
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import ApiError, InvalidEqPayLoad, InvalidURLSignature, JWTValidationError


logger = wrap_logger(logging.getLogger(__name__))


@app.errorhandler(404)
def not_found_error(error):
    logger.error('Not found error', url=request.url, status_code=error.code)
    return render_template('errors/404-error.html'), 404


@app.errorhandler(ApiError)
def api_error(error):
    logger.error(error.message or 'Api failed to retrieve required data',
                 url=request.url,
                 status_code=500,
                 api_url=error.url,
                 api_status_code=error.status_code,
                 **error.kwargs)
    return render_template('errors/500-error.html'), 500


@app.errorhandler(ConnectionError)
def connection_error(error):
    logger.error('Failed to connect to external service', url=request.url, status_code=500, api_url=error.request.url)
    return render_template('errors/500-error.html'), 500


@app.errorhandler(JWTValidationError)
def jwt_validation_error(error):  # pylint: disable=unused-argument
    logger.error('JWT validation error', url=request.url, status_code=403)
    return render_template('errors/not-signed-in.html'), 403


@app.errorhandler(Exception)
def server_error(error):
    logger.error('Generic exception generated', exc_info=error, url=request.url, status_code=500)
    return render_template('errors/500-error.html'), getattr(error, 'code', 500)


@app.errorhandler(InvalidEqPayLoad)
def eq_error(error):
    logger.error('Failed to generate EQ URL', error=error.message, url=request.url, status_code=500)
    return render_template('errors/500-error.html'), 500


@app.errorhandler(InvalidURLSignature)
def url_error(error):
    logger.error('Invalid URL signature', error=error.message, url=request.url, status_code=400)
    return render_template('errors/404-error.html'), 400
