import logging

import requests
from flask import current_app as app
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError, OAuth2Error


logger = wrap_logger(logging.getLogger(__name__))


def sign_in(username, password):
    logger.info('Attempting to retrieve OAuth2 token for sign-in')

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
        # This if statement will only be true if the 'oauth' service is the ras-rm-auth-service.  This is only
        # meant to be a temporary measure until the switch is made and the new auth service is used.  Once
        # the oauth2 service is switched off, we should look to tidy up the api of the auth service (As the service
        # doesn't need a /tokens endpoint if there are no tokens) and tidy up this services interaction with it.
        if response.status_code == 204:
            return {}
    except requests.exceptions.HTTPError:
        if response.status_code == 401:
            auth_error = response.json().get('detail', '')
            message = response.json().get('title', '')

            raise OAuth2Error(logger, response, log_level='warning', message=message, oauth2_error=auth_error)
        else:
            logger.error('Failed to retrieve OAuth2 token')
            raise ApiError(response)

    logger.info('Successfully retrieved OAuth2 token')
    return response.json()
