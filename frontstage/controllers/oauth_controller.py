import logging

from flask import current_app as app
import requests
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError, OAuth2Error


logger = wrap_logger(logging.getLogger(__name__))


def check_account_valid(username):
    logger.debug('Attempting to check if account is valid in OAuth2 service')

    url = f"{app.config['OAUTH_URL']}/api/v1/tokens/"
    data = {
        'grant_type': 'reset_password',
        'client_id': app.config['OAUTH_CLIENT_ID'],
        'client_secret': app.config['OAUTH_CLIENT_SECRET'],
        'username': username,
    }
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    }
    response = requests.post(url, headers=headers, auth=app.config['OAUTH_BASIC_AUTH'], data=data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 401:
            oauth2_error = response.json().get('detail', '')
            message = 'Authentication error in OAuth2 service'
            raise OAuth2Error(logger, response, log_level='warning', message=message, oauth2_error=oauth2_error)
        else:
            message = 'Failed to check if account is valid in OAuth2 service'
            raise ApiError(logger, response, log_level='exception', message=message)

    logger.debug('Successfully checked account state, account is valid')


def sign_in(username, password):
    logger.debug('Attempting to retrieve OAuth2 token for sign-in')

    url = f"{app.config['OAUTH_URL']}/api/v1/tokens/"
    data = {
        'grant_type': 'password',
        'client_id': app.config['OAUTH_CLIENT_ID'],
        'client_secret': app.config['OAUTH_CLIENT_SECRET'],
        'username': username,
        'password': password,
    }
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    }
    response = requests.post(url, headers=headers, auth=app.config['OAUTH_BASIC_AUTH'], data=data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 401:
            oauth2_error = response.json().get('detail', '')
            message = 'Authentication error in OAuth2 service'
            raise OAuth2Error(logger, response, log_level='warning', message=message, oauth2_error=oauth2_error)
        else:
            message = 'Failed to retrieve OAuth2 token'
            raise ApiError(logger, response, log_level='exception', message=message)

    logger.debug('Successfully retrieved OAuth2 token')
    return response.json()
