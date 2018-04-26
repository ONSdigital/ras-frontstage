import json
import logging

import arrow
from flask import current_app as app
from structlog import wrap_logger

from frontstage.common.request_handler import request_handler
from frontstage.controllers import collection_exercise_controller, collection_instrument_controller, party_controller, survey_controller
from frontstage.exceptions.exceptions import ApiError, InvalidCaseCategory, NoSurveyPermission


logger = wrap_logger(logging.getLogger(__name__))


def get_case_by_case_id(case_id):
    logger.debug('Retrieving case', case_id=case_id)
    url = f"{app.config['RM_CASE_SERVICE']}/cases/{case_id}"
    response = request_handler('GET', url, auth=app.config['BASIC_AUTH'])

    if response.status_code != 200:
        raise ApiError(url=url, status_code=response.status_code, description='Failed to retrieve case',
                       case_id=case_id)

    logger.debug('Successfully retrieved case', case_id=case_id)
    return json.loads(response.text)


def get_case_by_party_id(party_id, case_events=False):
    logger.debug('Retrieving case', party_id=party_id)
    url = f"{app.config['RM_CASE_SERVICE']}/cases/partyid/{party_id}"
    if case_events:
        url = f'{url}?caseevents=true'
    response = request_handler('GET', url, auth=app.config['BASIC_AUTH'])

    if response.status_code != 200:
        raise ApiError(url=url, status_code=response.status_code, description='Failed to retrieve case',
                       party_id=party_id)

    logger.debug('Successfully retrieved case', party_id=party_id)
    return json.loads(response.text)


def get_case_by_enrolment_code(enrolment_code):
    logger.debug('Retrieving case', enrolment_code=enrolment_code)
    url = f"{app.config['RM_CASE_SERVICE']}/cases/iac/{enrolment_code}"
    response = request_handler('GET', url, auth=app.config['BASIC_AUTH'])

    if response.status_code != 200:
        raise ApiError(url=url, status_code=response.status_code, description='Failed to retrieve case',
                       enrolment_code=enrolment_code)

    logger.debug('Successfully retrieved case', enrolment_code=enrolment_code)
    return json.loads(response.text)


def get_case_categories():
    logger.debug('Retrieving case categories')
    url = f"{app.config['RM_CASE_SERVICE']}/categories"
    response = request_handler('GET', url, auth=app.config['BASIC_AUTH'])

    if response.status_code != 200:
        raise ApiError(url=url, status_code=response.status_code, description='Failed to retrieve case categories')

    logger.debug('Successfully retrieved case categories')
    return json.loads(response.text)


def validate_case_category(category):
    logger.debug('Validating case category', category=category)
    categories = get_case_categories()
    category_names = [cat['name'] for cat in categories]
    if category not in category_names:
        raise InvalidCaseCategory(category)


def post_case_event(case_id, party_id, category, description):
    logger.debug('Posting case event', case_id=case_id)
    validate_case_category(category)
    url = f"{app.config['RM_CASE_SERVICE']}/cases/{case_id}/events"
    message = {
        'description': description,
        'category': category,
        'partyId': party_id,
        'createdBy': 'RAS_FRONTSTAGE_API'
    }
    response = request_handler('POST', url, auth=app.config['BASIC_AUTH'], json=message)

    if response.status_code != 201:
        raise ApiError(url=url, status_code=response.status_code, description='Failed to post to case service',
                       case_id=case_id)
    logger.debug('Successfully posted case event', case_id=case_id)


def check_case_permissions(party_id, case_party_id, case_id=None):
    logger.debug('Party requesting access to case', party_id=party_id, case_id=case_id, case_party_id=case_party_id)
    if party_id != case_party_id:
        raise NoSurveyPermission(party_id, case_id, case_party_id)

    logger.debug('Party has permission to access case', party_id=party_id, case_id=case_id, case_party_id=case_party_id)


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
