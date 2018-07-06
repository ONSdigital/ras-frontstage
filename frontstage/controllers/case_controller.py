import logging

import arrow
import requests
from flask import abort, current_app as app
from structlog import wrap_logger

from frontstage.common import eq_payload
from frontstage.common.encrypter import Encrypter
from frontstage.controllers import (collection_exercise_controller, collection_instrument_controller,
                                    party_controller, survey_controller)
from frontstage.exceptions.exceptions import ApiError, InvalidCaseCategory, NoSurveyPermission


logger = wrap_logger(logging.getLogger(__name__))


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


def calculate_case_status(case_group_status, collection_instrument_type):
    logger.debug('Getting the status of caseGroup', case_group_status=case_group_status,
                 collection_instrument_type=collection_instrument_type)

    status = 'Not started'

    if case_group_status == 'COMPLETE':
        status = 'Complete'
    elif case_group_status == 'COMPLETEDBYPHONE':
        status = 'Completed by phone'
    elif case_group_status == 'NOLONGERREQUIRED':
        status = 'No longer required'
    elif case_group_status == 'INPROGRESS' and collection_instrument_type == 'EQ':
        status = 'In progress'
    elif case_group_status == 'INPROGRESS' and collection_instrument_type == 'SEFT':
        status = 'Downloaded'

    logger.debug('Retrieved the status of case', collection_instrument_type=collection_instrument_type,
                 status=status)
    return status


def case_is_enrolled(case, respondent_id):
    logger.debug('Checking status of case for respondent', party_id=respondent_id)
    association = next((association
                       for association in case['business_party']['associations']
                       if association['partyId'] == respondent_id), {})
    enrolment_status = next((enrolment['enrolmentStatus']
                            for enrolment in association.get('enrolments', [])
                            if enrolment['surveyId'] == case['survey']['id']), '')
    if not enrolment_status:
        logger.warning('No status found for case', party_id=respondent_id)
    return enrolment_status == 'ENABLED'


def check_case_permissions(party_id, case_party_id, business_party_id, survey_short_name):
    logger.debug('Party requesting access to case', party_id=party_id, case_party_id=case_party_id, business_party_id=business_party_id, survey_short_name=survey_short_name)
    match = False

    party = party_controller.get_party_by_id(party_id)
    for association in party['associations']:
        if association['partyId'] == business_party_id:
            survey = survey_controller.get_survey_by_short_name(survey_short_name)
            for enrolment in association['enrolments']:
                if enrolment['surveyId'] == survey['id']:
                    match = True
    if not match:
        raise NoSurveyPermission(party_id, case_party_id)

    logger.debug('Party has permission to access case', party_id=party_id, case_party_id=case_party_id)


def format_collection_exercise_dates(collection_exercise):
    logger.debug('Formatting collection exercise dates')
    input_date_format = 'YYYY-MM-DDThh:mm:ss'
    output_date_format = 'D MMM YYYY'
    for key in ['periodStartDateTime', 'periodEndDateTime', 'scheduledReturnDateTime']:
        collection_exercise[key] = collection_exercise[key].replace('Z', '')
        collection_exercise[key + 'Formatted'] = arrow.get(collection_exercise[key], input_date_format).format(output_date_format)

    logger.debug('Successfully formatted collection exercise dates')
    return collection_exercise


def get_case_by_case_id(case_id):
    logger.debug('Attempting to retrieve case by case id', case_id=case_id)

    url = f"{app.config['CASE_URL']}/cases/{case_id}"
    response = requests.get(url, auth=app.config['CASE_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       case_id=case_id,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to retrieve case by case id')

    logger.debug('Successfully retrieved case by case id', case_id=case_id)
    return response.json()


def get_case_by_enrolment_code(enrolment_code):
    logger.debug('Attempting to retrieve case by enrolment code')

    url = f"{app.config['CASE_URL']}/cases/iac/{enrolment_code}"
    response = requests.get(url, auth=app.config['CASE_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to retrieve case by enrolment code')

    logger.debug('Successfully retrieved case by enrolment code')
    return response.json()


def get_case_categories():
    logger.debug('Attempting to retrieve case categories')

    url = f"{app.config['CASE_URL']}/categories"
    response = requests.get(url, auth=app.config['CASE_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to get case categories')

    logger.debug('Successfully retrieved case categories')
    return response.json()


def get_case_data(case_id, party_id, business_party_id, survey_short_name):
    logger.debug('Attempting to retrieve detailed case data', case_id=case_id, party_id=party_id)

    # Check if respondent has permission to see case data
    case = get_case_by_case_id(case_id)
    check_case_permissions(party_id, case['partyId'], business_party_id, survey_short_name)

    full_case_data = build_full_case_data(case)

    logger.debug('Successfully retrieved all data relating to case', case_id=case_id, party_id=party_id)
    return full_case_data


def get_case_id_for_group(case_list, case_group_id):
    logger.debug('Attempting to get case for group', case_group_id=case_group_id)

    if case_group_id:
        for case in case_list:
            if case_group_id == case.get('caseGroup', {}).get('id'):
                logger.debug('Successfully found case for group', case_group_id=case_group_id, case_id=case['id'])
                return case['id']


def get_cases_by_party_id(party_id, case_events=False):
    logger.debug('Attempting to retrieve cases by party id', party_id=party_id)

    url = f"{app.config['CASE_URL']}/cases/partyid/{party_id}"
    if case_events:
        url = f'{url}?caseevents=true'
    response = requests.get(url, auth=app.config['CASE_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to retrieve cases by party id',
                       party_id=party_id)

    logger.debug('Successfully retrieved cases by party id', party_id=party_id)
    return response.json()


def get_eq_url(case_id, party_id, business_party_id, survey_short_name):
    logger.debug('Attempting to generate EQ URL', case_id=case_id, party_id=party_id)

    case = get_case_by_case_id(case_id)

    if case['caseGroup']['caseGroupStatus'] == 'COMPLETE':
        logger.info('The case group status is complete, opening an EQ is forbidden',
                    case_id=case_id, party_id=party_id)
        abort(403)

    check_case_permissions(party_id, case['partyId'], business_party_id, survey_short_name)

    payload = eq_payload.EqPayload().create_payload(case)

    json_secret_keys = app.config['JSON_SECRET_KEYS']
    encrypter = Encrypter(json_secret_keys)
    token = encrypter.encrypt(payload)

    eq_url = app.config['EQ_URL'] + token

    category = 'EQ_LAUNCH'
    ci_id = case['collectionInstrumentId']
    post_case_event(case_id,
                    party_id=party_id,
                    category=category,
                    description=f"Instrument {ci_id} launched by {party_id} for case {case_id}")

    logger.debug('Successfully generated EQ URL', case_id=case_id, ci_id=ci_id, party_id=party_id,
                 business_party_id=business_party_id, survey_short_name=survey_short_name)
    return eq_url


def post_case_event(case_id, party_id, category, description):
    logger.debug('Posting case event', case_id=case_id)

    validate_case_category(category)
    url = f"{app.config['CASE_URL']}/cases/{case_id}/events"
    message = {
        'description': description,
        'category': category,
        'partyId': party_id,
        'createdBy': 'RAS_FRONTSTAGE'
    }
    response = requests.post(url, auth=app.config['CASE_AUTH'], json=message)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       case_id=case_id,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to post case event')

    logger.debug('Successfully posted case event', case_id=case_id)


def validate_case_category(category):
    logger.debug('Validating case category', category=category)

    categories = get_case_categories()
    category_names = [cat['name'] for cat in categories]
    if category not in category_names:
        raise InvalidCaseCategory(category)

    logger.debug('Successfully validated case category', category=category)


def get_cases_for_list_type_by_party_id(party_id, list_type='todo'):
    logger.debug('Get cases for party for list', party_id=party_id, list_type=list_type)

    business_cases = get_cases_by_party_id(party_id)

    history_statuses = ['COMPLETE', 'COMPLETEDBYPHONE', 'NOLONGERREQUIRED']
    if list_type == 'history':
        filtered_cases = [business_case
                          for business_case in business_cases
                          if business_case.get('caseGroup', {}).get('caseGroupStatus') in history_statuses]
    else:
        filtered_cases = [business_case
                          for business_case in business_cases
                          if business_case.get('caseGroup', {}).get('caseGroupStatus') not in history_statuses]

    logger.debug("Sucessfully retrieved cases for party survey list", party_id=party_id, list_type=list_type)
    return filtered_cases
