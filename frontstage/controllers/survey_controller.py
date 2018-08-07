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


def enrolment_with_survey(enrolment, surveys):
    survey = next(survey for survey in surveys if enrolment["enrolment_details"]["surveyId"] == survey['id'])
    return {**enrolment, "survey": survey}


def get_surveys_with_enrolments(enrolments):
    survey_ids = {enrolment['enrolment_details']['surveyId']
                  for enrolment in enrolments}
    surveys = [get_survey(survey_id) for survey_id in survey_ids]
    return [enrolment_with_survey(enrolment, surveys) for enrolment in enrolments]
