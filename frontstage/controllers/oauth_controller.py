import logging

from flask import current_app as app
import requests
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError, OAuth2Error


logger = wrap_logger(logging.getLogger(__name__))


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
            logger.exception('Authentication error in oauth2 service', error=oauth2_error)
            raise OAuth2Error(response, message=oauth2_error)
        else:
            logger.exception('Failed to retrieve OAuth2 token')
        raise ApiError(response)

    logger.debug('Successfully retrieved OAuth2 token')
    return response.json()
