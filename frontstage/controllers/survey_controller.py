import logging

from flask import current_app as app
import requests
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError


logger = wrap_logger(logging.getLogger(__name__))


def get_survey(survey_id):
    logger.debug('Attempting to retrieve survey', survey_id=survey_id)
    url = f"{app.config['SURVEY_URL']}/surveys/{survey_id}"
    response = requests.get(url, auth=app.config['SURVEY_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.exception('Failed to retrieve survey', survey_id=survey_id)
        raise ApiError(response)

    logger.debug('Successfully retrieved survey', survey_id=survey_id)
    return response.json()
