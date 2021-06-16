import logging

import requests
from flask import current_app as app
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError


logger = wrap_logger(logging.getLogger(__name__))


def get_survey(survey_url, survey_auth, survey_id):
    logger.info('Attempting to retrieve survey', survey_id=survey_id)
    url = f"{survey_url}/surveys/{survey_id}"
    response = requests.get(url, auth=survey_auth)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error('Failed to retrieve survey', survey_id=survey_id)
        raise ApiError(logger, response)

    logger.info('Successfully retrieved survey', survey_id=survey_id)
    return response.json()


def get_survey_by_short_name(survey_short_name):
    logger.info('Attempting to retrieve survey by its short name', survey_short_name=survey_short_name)
    url = f"{app.config['SURVEY_URL']}/surveys/shortname/{survey_short_name}"
    response = requests.get(url, auth=app.config['BASIC_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error('Failed to retrieve survey by its short name', survey_short_name=survey_short_name)
        raise ApiError(logger, response)

    logger.info('Successfully retrieved survey by its short name', survey_short_name=survey_short_name)
    return response.json()

def get_survey_by_survey_ref(survey_ref):
    logger.info('Attempting to retrieve survey by its survey ref', survey_ref=survey_ref)
    url = f"{app.config['SURVEY_URL']}/surveys/ref/{survey_ref}"
    response = requests.get(url, auth=app.config['BASIC_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error('Failed to retrieve survey by its survey ref', survey_ref=survey_ref)
        raise ApiError(logger, response)

    logger.info('Successfully retrived survey by its survey ref', survey_ref=survey_ref)
    return response.json()