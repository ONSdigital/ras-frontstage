import json
import logging

from flask import current_app as app
import requests
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError


logger = wrap_logger(logging.getLogger(__name__))


def get_party_by_email(email):
    logger.debug('Retrieving party')
    url = f"{app.config['PARTY_SERVICE_URL']}/party-api/v1/respondents/email"
    response = requests.get(url, json={"email": email}, auth=app.config['BASIC_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.exception('Failed to retrieve party')
        raise ApiError(response)

    logger.debug('Successfully retrieved party')
    return json.loads(response.text)
