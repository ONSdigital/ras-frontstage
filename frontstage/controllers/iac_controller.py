import functools
import logging

from flask import current_app as app
import requests
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError


logger = wrap_logger(logging.getLogger(__name__))


def get_iac_from_enrolment(enrolment_code, validate=False):
    logger.debug('Attempting to retrieve IAC', enrolment_code=enrolment_code)
    url = f"{app.config['IAC_URL']}/iacs/{enrolment_code}"
    response = requests.get(url, auth=app.config['IAC_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            logger.warning('IAC not found', enrolment_code=enrolment_code)
            if validate:
                logger.error('Invalid enrolment code used', enrolment_code=enrolment_code)
                raise ApiError(response)
            return
        elif response.status_code != 401:
            logger.exception('Failed to retrieve IAC', enrolment_code=enrolment_code)
            raise ApiError(response)

    if validate and not response.json().get('active', False):
        logger.error('Invalid enrolment code used', enrolment_code=enrolment_code)
        raise ApiError(response)

    logger.debug('Successfully retrieved IAC', enrolment_code=enrolment_code)
    return response.json()


validate_enrolment_code = functools.partial(get_iac_from_enrolment, validate=True)
