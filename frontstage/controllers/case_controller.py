import logging

import arrow
from flask import current_app as app
import requests
from structlog import wrap_logger

from frontstage.controllers import collection_exercise_controller, collection_instrument_controller, party_controller, survey_controller
from frontstage.exceptions.exceptions import ApiError, NoSurveyPermission


logger = wrap_logger(logging.getLogger(__name__))


def get_case_by_case_id(case_id):
    logger.debug('Retrieving case', case_id=case_id)
    url = f"{app.config['CASE_SERVICE_URL']}/cases/{case_id}"
    response = requests.get(url, auth=app.config['BASIC_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.exception('Failed to retrieve case', case_id=case_id)
        raise ApiError(response)

    logger.debug('Successfully retrieved case', case_id=case_id)
    return response.json()


def check_case_permissions(party_id, case_party_id, case_id=None):
    logger.debug('Party requesting access to case', party_id=party_id, case_id=case_id, case_party_id=case_party_id)
    if party_id != case_party_id:
        raise NoSurveyPermission(party_id, case_id, case_party_id)

    logger.debug('Party has permission to access case', party_id=party_id, case_id=case_id, case_party_id=case_party_id)


def get_case_data(case_id, party_id):
    logger.debug('Attempting to retrieve detailed case data', case_id=case_id, party_id=party_id)

    # Check if respondent has permission to see case data
    case = get_case_by_case_id(case_id)
    check_case_permissions(party_id, case['partyId'], case_id=case_id)

    full_case_data = build_full_case_data(case)

    logger.debug('Successfully retrieved all data relating to case', case_id=case_id, party_id=party_id)
    return full_case_data


def build_full_case_data(case):
    logger.debug('Attempting to build case data', case_id=case['id'])
    collection_exercise_id = case["caseGroup"]["collectionExerciseId"]
    collection_exercise = collection_exercise_controller.get_collection_exercise(collection_exercise_id)
    collection_exercise_formatted = format_collection_exercise_dates(collection_exercise)
    collection_exercise_go_live = collection_exercise_controller.get_collection_exercise_event(collection_exercise_id, 'go_live')

    business_party_id = case['caseGroup']['partyId']
    business_party = party_controller.get_party_by_business_id(business_party_id,
                                                               collection_exercise_id=collection_exercise_id)
    survey_id = collection_exercise['surveyId']
    survey = survey_controller.get_survey(survey_id)

    collection_instrument = collection_instrument_controller \
        .get_collection_instrument(case['collectionInstrumentId'])

    status = calculate_case_status(case, collection_instrument['type'])
    survey_data = {
        "case": case,
        "collection_exercise": collection_exercise_formatted,
        "business_party": business_party,
        "survey": survey,
        "status": status,
        "collection_instrument_type": collection_instrument['type'],
        "collection_instrument_size": collection_instrument['len'],
        "go_live": collection_exercise_go_live
    }
    logger.debug('Successfully built case data', case_id=case['id'])
    return survey_data


def calculate_case_status(case, collection_instrument_type):
    logger.debug('Getting the status of case')
    status = 'Not started'
    case_group_status = case.get('caseGroup', {}).get('caseGroupStatus')

    if case_group_status == 'COMPLETE':
        status = 'Complete'
    elif case_group_status == 'COMPLETEDBYPHONE':
        status = 'Completed by phone'
    elif case_group_status == 'INPROGRESS' and collection_instrument_type == 'EQ':
        status = 'In progress'
    elif case_group_status == 'INPROGRESS' and collection_instrument_type == 'SEFT':
        status = 'Downloaded'

    logger.debug('Retrieved the status of case', status=status)
    return status


def format_collection_exercise_dates(collection_exercise):
    logger.debug('Formatting collection exercise dates')
    input_date_format = 'YYYY-MM-DDThh:mm:ss'
    output_date_format = 'D MMM YYYY'
    for key in ['periodStartDateTime', 'periodEndDateTime', 'scheduledReturnDateTime']:
        collection_exercise[key] = collection_exercise[key].replace('Z', '')
        collection_exercise[key + 'Formatted'] = arrow.get(collection_exercise[key], input_date_format).format(output_date_format)
    logger.debug('Successfully formatted collection exercise dates')
    return collection_exercise
