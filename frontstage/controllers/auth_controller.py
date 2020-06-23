import logging

import requests
from flask import current_app as app
from structlog import wrap_logger

from frontstage.common.utilities import obfuscate_email
from frontstage.exceptions.exceptions import ApiError, AuthError


logger = wrap_logger(logging.getLogger(__name__))


def sign_in(username, password):
    bound_logger = logger.bind(email=obfuscate_email(username))
    bound_logger.info('Attempting to sign in')

    url = f"{app.config['AUTH_URL']}/api/v1/tokens/"
    data = {
        'username': username,
        'password': password,
    }
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    }
    response = requests.post(url, headers=headers, auth=app.config['BASIC_AUTH'], data=data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        auth_error = response.json().get('detail', '')
        message = response.json().get('title', '')
        bound_logger.error('Failed to authenticate')
        raise AuthError(logger, response, log_level='warning', message=message, auth_error=auth_error)

    bound_logger.info('Successfully signed in')
    return {}
