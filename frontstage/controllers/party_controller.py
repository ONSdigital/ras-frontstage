import logging
import requests

from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import ApiError

logger = wrap_logger(logging.getLogger(__name__))


def get_respondent_by_email(email):
    logger.debug("Attempting to find respondent party by email")

    url = f'{app.config["PARTY_URL"]}/party-api/v1/respondents/email'
    response = requests.get(url, json={"email": email}, auth=(app.config['PARTY_AUTH']))

    if response.status_code == 404:
        return

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.exception("Error retrieving respondent by email")
        raise ApiError(response)

    logger.debug("Successfully retrieved respondent by email")
    return response.json()
