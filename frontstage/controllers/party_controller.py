import logging

from flask import current_app as app
import requests
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError


logger = wrap_logger(logging.getLogger(__name__))


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
