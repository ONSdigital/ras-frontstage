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
                message = 'Invalid enrolment code used'
                raise ApiError(logger, response, enrolment_code=enrolment_code, message=message)
            return
        # 401s may include error context in the JSON response
        elif response.status_code != 401:
            raise ApiError(logger, response, enrolment_code=enrolment_code, message='Failed to retrieve IAC')

    if validate and not response.json().get('active', False):
        raise ApiError(logger, response, enrolment_code=enrolment_code, message='Invalid enrolment code used')

    logger.debug('Successfully retrieved IAC', enrolment_code=enrolment_code)
    return response.json()


validate_enrolment_code = functools.partial(get_iac_from_enrolment, validate=True)
