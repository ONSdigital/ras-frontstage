import logging

import requests
from flask import current_app as app
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
        raise ApiError(logger, response,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to retrieve survey',
                       survey_id=survey_id)

    logger.debug('Successfully retrieved survey', survey_id=survey_id)
    return response.json()

def get_survey_with_config(config, survey_id):
    logger.debug('Attempting to retrieve survey', survey_id=survey_id)
    url = f"{config['SURVEY_URL']}/surveys/{survey_id}"
    response = requests.get(url, auth=config['SURVEY_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to retrieve survey',
                       survey_id=survey_id)

    logger.debug('Successfully retrieved survey', survey_id=survey_id)
    return response.json()


def get_survey_by_short_name(survey_short_name):
    logger.debug('Attempting to retrieve survey by its short name', survey_short_name=survey_short_name)
    url = f"{app.config['SURVEY_URL']}/surveys/shortname/{survey_short_name}"
    response = requests.get(url, auth=app.config['SURVEY_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to retrieve survey by its short name',
                       survey_short_name=survey_short_name)

    logger.debug('Successfully retrieved survey by its short name', survey_short_name=survey_short_name)
    return response.json()
