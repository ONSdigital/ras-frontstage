import logging

from flask import render_template, request, url_for
from flask_wtf.csrf import CSRFError
from requests.exceptions import ConnectionError
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage import app
from frontstage.common.session import Session
from frontstage.exceptions.exceptions import ApiError, InvalidEqPayLoad, JWTValidationError, IncorrectAccountAccessError

logger = wrap_logger(logging.getLogger(__name__))


@app.errorhandler(400)
def client_error(error):
    logger.info('Client error', url=request.url, status_code=error.code)
    return render_template('errors/400-error.html'), 400


@app.errorhandler(404)
def not_found_error(error):
    logger.info('Not found error', url=request.url, status_code=error.code)
    return render_template('errors/404-error.html'), 404


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    logger.warning('CSRF token has expired', error_message=error.description, status_code=error.code)

    session_key = request.cookies.get('authorization')
    session_handler = Session.from_session_key(session_key)
    encoded_jwt = session_handler.get_encoded_jwt()
    if not encoded_jwt:
        return render_template('errors/400-error.html'), 400
    else:
        return redirect(url_for('sign_in_bp.logout', csrf_error=True, next=request.url))


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
    return render_template('errors/403-error.html'), 403


@app.errorhandler(Exception)
def server_error(error):
    logger.error('Generic exception generated', exc_info=error, url=request.url, status_code=500)
    return render_template('errors/500-error.html'), getattr(error, 'code', 500)


@app.errorhandler(InvalidEqPayLoad)
def eq_error(error):
    logger.error('Failed to generate EQ URL', error=error.message, url=request.url, status_code=500)
    return render_template('errors/500-error.html'), 500


@app.errorhandler(IncorrectAccountAccessError)
def secure_message_forbidden_error(error):
    logger.info('Attempt to access secure message without correct session permission', url=request.url,
                message=error.message, thread_id=error.thread)
    return render_template('errors/403-incorrect-account-error.html')
