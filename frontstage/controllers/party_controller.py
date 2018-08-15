import logging

import requests
from flask import current_app as app
from structlog import wrap_logger

from frontstage.controllers import case_controller, collection_exercise_controller, collection_instrument_controller, survey_controller
from frontstage.exceptions.exceptions import ApiError


logger = wrap_logger(logging.getLogger(__name__))


def get_respondent_party_by_id(party_id):
    logger.debug('Retrieving party from party service by id', party_id=party_id)

    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/id/{party_id}"
    response = requests.get(url, auth=app.config['PARTY_AUTH'])

    if response.status_code == 404:
        return

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       message='Failed to find respondent',
                       party_id=party_id)

    logger.debug('Successfully retrieved party details', party_id=party_id)
    return response.json()


def add_survey(party_id, enrolment_code):
    logger.debug('Attempting to add a survey', party_id=party_id)

    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/add_survey"
    request_json = {'party_id': party_id, 'enrolment_code': enrolment_code}
    response = requests.post(url, auth=app.config['PARTY_AUTH'], json=request_json)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       log_level='warning' if response.status_code == 404 else 'error',
                       message='Failed to add a survey',
                       party_id=party_id)

    logger.debug('Successfully added a survey', party_id=party_id)


def change_password(password, token):
    logger.debug('Attempting to change password through the party service')

    data = {'new_password': password}
    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/change_password/{token}"
    response = requests.put(url, auth=app.config['PARTY_AUTH'], json=data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to send change password request to party service',
                       token=token)

    logger.debug('Successfully changed password through the party service')


def create_account(registration_data):
    logger.debug('Attempting to create account')

    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents"
    registration_data['status'] = 'CREATED'
    response = requests.post(url, auth=app.config['PARTY_AUTH'], json=registration_data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 400:
            message = 'Email has already been used'
        else:
            message = 'Failed to create account'
        raise ApiError(logger, response,
                       log_level='debug' if response.status_code == 400 else 'error',
                       message=message)

    logger.debug('Successfully created account')


def get_party_by_business_id(party_id, collection_exercise_id=None):
    logger.debug('Attempting to retrieve party by business', party_id=party_id)

    url = f"{app.config['PARTY_URL']}/party-api/v1/businesses/id/{party_id}"
    if collection_exercise_id:
        url += f"?collection_exercise_id={collection_exercise_id}&verbose=True"
    response = requests.get(url, auth=app.config['PARTY_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       collection_exercise_id=collection_exercise_id,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to retrieve party by business',
                       party_id=party_id)

    logger.debug('Successfully retrieved party by business',
                 collection_exercise_id=collection_exercise_id,
                 party_id=party_id)
    return response.json()


def get_respondent_by_email(email):
    logger.debug('Attempting to find respondent party by email')

    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/email"
    response = requests.get(url, json={"email": email}, auth=app.config['PARTY_AUTH'])

    if response.status_code == 404:
        logger.debug('Failed to retrieve party by email')
        return

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response, message='Error retrieving respondent by email')

    logger.debug('Successfully retrieved respondent by email')
    return response.json()


def reset_password_request(username):
    logger.debug('Attempting to send reset password request to party service')

    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/request_password_change"
    data = {"email_address": username}
    response = requests.post(url, auth=app.config['PARTY_AUTH'], json=data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        log_level = 'warning' if response.status_code == 404 else 'exception'
        message = 'Failed to send reset password request to party service'
        raise ApiError(logger, response, log_level=log_level, message=message)

    logger.debug('Successfully sent reset password request to party service')


def verify_email(token):
    logger.debug('Attempting to verify email address', token=token)

    url = f"{app.config['PARTY_URL']}/party-api/v1/emailverification/{token}"
    response = requests.put(url, auth=app.config['PARTY_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        log_level = 'warning' if response.status_code == 404 else 'error'
        raise ApiError(logger, response, log_level=log_level, message='Failed to verify email', token=token)

    logger.debug('Successfully verified email address', token=token)


def verify_token(token):
    logger.debug('Attempting to verify token with party service')

    url = f"{app.config['PARTY_URL']}/party-api/v1/tokens/verify/{token}"
    response = requests.get(url, auth=app.config['PARTY_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        log_level = 'warning' if response.status_code == 404 else 'error'
        raise ApiError(logger, response, log_level=log_level, message='Failed to verify token', token=token)

    logger.debug('Successfully verified token')


def get_respondent_enrolments(party_id):
    respondent = get_respondent_party_by_id(party_id)
    for association in respondent['associations']:
        for enrolment in association['enrolments']:
            if enrolment['enrolmentStatus'] == 'ENABLED':
                yield {
                    'business_id': association['partyId'],
                    'survey_id': enrolment['surveyId']
                }


def get_survey_list_details_for_party(party_id, tag):

    for enrolment in get_respondent_enrolments(party_id):
        business_id = enrolment['business_id']
        survey_id = enrolment['survey_id']

        live_collection_exercises = collection_exercise_controller.get_live_collection_exercises_for_survey(survey_id)
        collection_exercises_by_id = dict((ce['id'], ce) for ce in live_collection_exercises)

        cases = case_controller.get_cases_for_list_type_by_party_id(business_id, tag)
        enrolled_cases = [case for case in cases if case['caseGroup']['collectionExerciseId'] in collection_exercises_by_id.keys()]

        for case in enrolled_cases:
            collection_instrument = collection_instrument_controller.get_collection_instrument(
                case['collectionInstrumentId']
            )
            survey = survey_controller.get_survey(survey_id)
            yield {
                'case_id': case['id'],
                'status': case_controller.calculate_case_status(case['caseGroup']['caseGroupStatus'],
                                                                collection_instrument['type']),
                'collection_instrument_type': collection_instrument['type'],
                'survey_id': survey_id,
                'survey_long_name': survey['longName'],
                'survey_short_name': survey['shortName'],
                'survey_ref': survey['surveyRef'],
                'business_party': get_party_by_business_id(business_id),
                'collection_exercise': collection_exercises_by_id[case['caseGroup']['collectionExerciseId']]
            }


def is_respondent_enrolled(party_id, business_party_id, survey_short_name):
    survey = survey_controller.get_survey_by_short_name(survey_short_name)
    for enrolment in get_respondent_enrolments(party_id):
        if enrolment['business_id'] == business_party_id and enrolment['survey_id'] == survey['id']:
            return True
