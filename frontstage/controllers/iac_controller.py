import functools
import logging

from flask import current_app as app
import requests
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError


logger = wrap_logger(logging.getLogger(__name__))


def get_iac_from_enrolment(enrolment_code, validate=False):
    logger.debug('Attempting to retrieve IAC')
    url = f"{app.config['IAC_URL']}/iacs/{enrolment_code}"
    response = requests.get(url, auth=app.config['IAC_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            logger.info('IAC not found')
            if validate:
                raise ApiError(logger.info, response, message='Invalid enrolment code used')
            return
        # 401s may include error context in the JSON response
        elif response.status_code != 401:
            raise ApiError(logger, response, message='Failed to retrieve IAC')

    if validate and not response.json().get('active', False):
        raise ApiError(logger.info, response, message='Invalid enrolment code used')

    logger.info('Successfully retrieved IAC')
    return response.json()


validate_enrolment_code = functools.partial(get_iac_from_enrolment, validate=True)
