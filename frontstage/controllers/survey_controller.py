import logging
from datetime import datetime, timezone

import requests
from flask import current_app as app
from iso8601 import parse_date
from structlog import wrap_logger

from frontstage.controllers import case_controller
from frontstage.exceptions.exceptions import ApiError, InvalidSurveyList


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


def get_surveys_list(cases, party_id, list_type):
    logger.info('Attempting to retrieve surveys list', party_id=party_id, list_type=list_type)

    if list_type == 'todo':
        filtered_cases = [case
                          for case in cases
                          if case.get('caseGroup', {}).get('caseGroupStatus') not in ['COMPLETE', 'COMPLETEDBYPHONE']]
    elif list_type == 'history':
        filtered_cases = [case
                          for case in cases
                          if case.get('caseGroup', {}).get('caseGroupStatus') in ['COMPLETE', 'COMPLETEDBYPHONE']]
    else:
        logger.error('Invalid list type', party_id=party_id, list_type=list_type)
        raise InvalidSurveyList(list_type)

    surveys_data = [case_controller.build_full_case_data(case) for case in filtered_cases]
    now = datetime.now(timezone.utc)
    live_cases = [survey for survey in surveys_data if parse_date(survey['go_live']['timestamp']) < now]
    enrolled_cases = [case for case in live_cases if case_controller.case_is_enrolled(case, party_id)]

    logger.info('Successfully retrieved surveys list', party_id=party_id, list_type=list_type)
    return enrolled_cases
