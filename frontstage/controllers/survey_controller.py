import json
import logging

from flask import current_app as app
from structlog import wrap_logger

from frontstage.common.request_handler import request_handler
from frontstage.exceptions.exceptions import ApiError


logger = wrap_logger(logging.getLogger(__name__))


def get_survey(survey_id):
    logger.debug('Retrieving survey', survey_id=survey_id)
    url = f"{app.config['RM_SURVEY_SERVICE']}/surveys/{survey_id}"
    response = request_handler('GET', url, auth=app.config['BASIC_AUTH'])

    if response.status_code != 200:
        raise ApiError(url=url, status_code=response.status_code, description='Failed to retrieve survey',
                       survey_id=survey_id)

    logger.debug('Successfully retrieved survey', survey_id=survey_id)
    return json.loads(response.text)
