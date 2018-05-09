import logging

from flask import current_app as app
import requests
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError


logger = wrap_logger(logging.getLogger(__name__))


def add_survey(party_id, enrolment_code):
    logger.debug('Attempting to add a survey', party_id=party_id, enrolment_code=enrolment_code)
    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/add_survey"
    request_json = {"party_id": party_id, "enrolment_code": enrolment_code}
    response = requests.post(url, auth=app.config['PARTY_AUTH'], json=request_json)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error('Failed to add a survey', party_id=party_id, enrolment_code=enrolment_code)
        raise ApiError(response)

    logger.debug('Successfully added a survey', party_id=party_id, enrolment_code=enrolment_code)


def create_account(registration_data):
    enrolment_code = registration_data.get('enrolment_code')
    logger.debug('Attempting to create account', enrolment_code=enrolment_code)
    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents"
    registration_data['status'] = 'CREATED'
    response = requests.post(url, auth=app.config['PARTY_AUTH'], json=registration_data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 400:
            logger.debug('Email has already been used', enrolment_code=enrolment_code)
        else:
            logger.error('Failed to create account', enrolment_code=enrolment_code)
        raise ApiError(response)

    logger.debug('Successfully created account', enrolment_code=enrolment_code)


def get_party_by_business_id(party_id, collection_exercise_id=None):
    logger.debug('Attempting to retrieve party by business',
                 collection_exercise_id=collection_exercise_id,
                 party_id=party_id)

    url = f"{app.config['PARTY_URL']}/party-api/v1/businesses/id/{party_id}"
    if collection_exercise_id:
        url += f"?collection_exercise_id={collection_exercise_id}&verbose=True"
    response = requests.get(url, auth=app.config['PARTY_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        log_level = logger.warning if response.status_code == 404 else logger.exception
        log_level('Failed to retrieve party',
                  collection_exercise_id=collection_exercise_id,
                  party_id=party_id)
        raise ApiError(response)

    logger.debug('Successfully retrieved party by business',
                 collection_exercise_id=collection_exercise_id,
                 party_id=party_id)
    return response.json()


def verify_email(token):
    logger.debug('Attempting to verify email address', token=token)

    url = f"{app.config['PARTY_URL']}/party-api/v1/emailverification/{token}"
    response = requests.put(url, auth=app.config['PARTY_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error('Failed to verify email', token=token)
        raise ApiError(response)

    logger.debug('Successfully verified email address', token=token)
