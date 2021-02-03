import logging
import requests

from flask import current_app as app
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))


def current_banner():
    """
    Calls the banner service to get the currently active banner.  This function logs very little by design as
    it's going to be called a lot and we don't want to spam the logs.

    :return: The banner text, if any, else an empty string
    """
    url = f"{app.config['BANNER_SERVICE_URL']}/banner"
    response = requests.get(url)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code != 404:
            logger.error('Failed to retrieve Banner from api')
        return ""

    banner = response.json()
    content = banner.get('content', "")
    return content
