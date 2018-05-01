import logging

from flask import current_app as app
import requests
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError, OAuth2Error


logger = wrap_logger(logging.getLogger(__name__))


def check_account_valid(username):
    logger.debug('Attempting to check if account is valid in OAuth2 service')

    url = f"{app.config['OAUTH_SERVICE_URL']}/api/v1/tokens/"
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
            oauth2_error = response.json().get('detail')
            logger.exception('Authentication error in OAuth2 service', error=oauth2_error)
            raise OAuth2Error(response, message=oauth2_error)
        else:
            logger.exception('Failed to check if account is valid in OAuth2 service')
        raise ApiError(response)

    logger.debug('Successfully checked account state, account is valid')
