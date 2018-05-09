import logging

from flask import current_app as app
import requests
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError


logger = wrap_logger(logging.getLogger(__name__))


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
        logger.exception('Error retrieving respondent by email')
        raise ApiError(response)

    logger.debug('Successfully retrieved respondent by email')
    return response.json()


def change_password(password, token):
    logger.debug('Attempting to change password through the party service')

    data = {"new_password": password}
    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/change_password/{token}"
    response = requests.put(url, auth=app.config['PARTY_AUTH'], json=data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        log_level = logger.warning if response.status_code == 404 else logger.exception
        log_level('Failed to send change password request to party service', token=token)
        raise ApiError(response)

    logger.debug('Successfully changed password through the party service')


def reset_password_request(username):
    logger.debug('Attempting to send reset password request to party service')

    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/request_password_change"
    data = {"email_address": username}
    response = requests.post(url, auth=app.config['PARTY_AUTH'], json=data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        log_level = logger.warning if response.status_code == 404 else logger.exception
        log_level('Failed to send reset password request to party service')
        raise ApiError(response)

    logger.debug('Successfully sent reset password request to party service')


def verify_token(token):
    logger.debug('Attempting to verify token with party service')

    url = f"{app.config['PARTY_URL']}/party-api/v1/tokens/verify/{token}"
    response = requests.get(url, auth=app.config['PARTY_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        log_level = logger.warning if response.status_code == 404 else logger.exception
        log_level('Failed to verify token', token=token)
        raise ApiError(response)

    logger.debug('Successfully verified token')
