import logging

import requests
from flask import current_app as app
from structlog import wrap_logger

from frontstage.common.list_helper import flatten_list
from frontstage.controllers import case_controller, collection_exercise_controller, survey_controller
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


def get_enrolment_details(business_party_id, enrolments):
    logger.debug("Attempt to retrieve enrolment details for association",
                 business_party_id=business_party_id)
    business_details = get_party_by_business_id(business_party_id)
    logger.debug("Successfully retrieved enrolment details for association",
                 business_party_id=business_party_id)
    return [{"business_party": business_details, "enrolment_details": enrolment}
            for enrolment in enrolments
            if enrolment['enrolmentStatus'] == 'ENABLED']


def get_respondent_enrolments(respondent):
    logger.debug("Attempt to retrieve respondent enrolments",
                 party_id=respondent['id'])
    enrolments = [get_enrolment_details(association['partyId'], association['enrolments'])
                  for association in respondent['associations']]
    logger.debug("Successfully retrieved enrolments for respondent",
                 party_id=respondent['id'])
    return flatten_list(enrolments)


def get_survey_list_details_for_party(party_id, tag):
    logger.debug("Attempt to retrieve survey list details for respondent",
                 party_id=party_id, list_type=tag)

    respondent = get_respondent_party_by_id(party_id)
    enrolments = get_respondent_enrolments(respondent)
    enrolments_with_surveys = survey_controller.get_surveys_with_enrolments(enrolments)
    enrolments_with_ces = collection_exercise_controller.get_enrolments_with_collection_exercises(enrolments_with_surveys)
    enrolments_with_cases = case_controller.get_enrolments_with_cases(enrolments_with_ces, tag)

    logger.debug("Successfully retrieved survey list details for respondent",
                 party_id=party_id, list_type=tag)

    return enrolments_with_cases
