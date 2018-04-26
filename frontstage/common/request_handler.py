import logging

import requests
from requests.exceptions import ConnectionError
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError, InvalidRequestMethod


logger = wrap_logger(logging.getLogger(__name__))


def request_handler(method, url, auth=None, headers=None, json=None, data=None, files=None, fail=True):
    try:
        if method == 'GET':
            response = requests.get(url, json=json, auth=auth, headers=headers)
        elif method == 'POST':
            response = requests.post(url, auth=auth, headers=headers, json=json, data=data, files=files)
        elif method == 'PUT':
            response = requests.put(url, auth=auth, headers=headers, json=json)
        else:
            logger.error('Invalid request method', method=str(method), url=url)
            raise InvalidRequestMethod(method, url)
    except ConnectionError:
        logger.exception('Failed to connect to external service', method=method, url=url)
        # If specified not to fail on this request just return False
        if fail:
            raise ApiError(url)
        else:
            return False

    return response
