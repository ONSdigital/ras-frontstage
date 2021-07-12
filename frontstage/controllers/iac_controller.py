import functools
import logging

import requests
from flask import current_app as app
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError

logger = wrap_logger(logging.getLogger(__name__))


def get_iac_from_enrolment(enrolment_code):
    """
    Gets enrolment details from IAC service for a given enrolment code

    :param enrolment_code: An enrolment code
    :type enrolment_code: str
    :raises ApiError: Raised when IAC service returns a 401 status
    :return: A dict with the IAC details if it exists and is active, and None otherwise
    """
    bound_logger = logger.bind(enrolment_code=enrolment_code)
    bound_logger.info("Attempting to retrieve IAC")
    url = f"{app.config['IAC_URL']}/iacs/{enrolment_code}"
    response = requests.get(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            bound_logger.info("IAC not found", status_code=response.status_code)
            return
        # 401s may include error context in the JSON response
        if response.status_code != 401:
            bound_logger.error("Failed to retrieve IAC")
            raise ApiError(logger, response)

    if response.json().get("active") is False:
        bound_logger.info("IAC is not active")
        return

    bound_logger.info("Successfully retrieved IAC")
    return response.json()


validate_enrolment_code = functools.partial(get_iac_from_enrolment)
