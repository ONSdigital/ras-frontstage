import logging

import requests
from flask import current_app as app
from structlog import wrap_logger

from frontstage.common.utilities import obfuscate_email
from frontstage.exceptions.exceptions import ApiError, AuthError

logger = wrap_logger(logging.getLogger(__name__))


def sign_in(username, password):
    """
    Checks if the users credentials are valid. On success, it returns an empty dict (a hangover from when
    this function used to call a different authentication application).

    :param username: The username.  Should be an email address
    :param password: The password
    :raises AuthError: Raised if the credentials provided are incorrect
    :raises ApiError: Raised on any other non-401 error status code
    :return: An empty dict if credentials are valid.  An exception is raised otherwise
    """
    if app.config["CANARY_GENERATE_ERRORS"]:
        logger.error("Canary experiment running this error can be ignored", status=500)
    logger.info("Attempting to sign in", email=obfuscate_email(username))

    url = f"{app.config['AUTH_URL']}/api/v1/tokens/"
    data = {
        "username": username,
        "password": password,
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    }
    response = requests.post(url, headers=headers, auth=app.config["BASIC_AUTH"], data=data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 401:
            auth_error = response.json().get("detail", "")
            message = response.json().get("title", "")

            raise AuthError(logger, response, log_level="warning", message=message, auth_error=auth_error)
        else:
            logger.error("Failed to authenticate", email=obfuscate_email(username), exc_info=True)
            raise ApiError(logger, response)
    # This log is associated with a custom log metric
    logger.info("Successfully signed in", email=obfuscate_email(username))
    return {}


def delete_account(username: str):
    bound_logger = logger.bind(email=obfuscate_email(username))
    bound_logger.info("Attempting to delete account")
    url = f'{app.config["AUTH_URL"]}/api/account/user'
    # force_delete will always be true if deletion is initiated by user
    form_data = {"username": username, "force_delete": True}
    response = requests.delete(url, data=form_data, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        bound_logger.error("Failed to delete account")
        bound_logger.unbind("email")
        raise ApiError(logger, response)

    bound_logger.info("Successfully deleted account")
    bound_logger.unbind("email")
    return response
