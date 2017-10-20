import logging

import requests
from requests.exceptions import ConnectionError, ConnectTimeout
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import FailedRequest, InvalidRequestMethod


logger = wrap_logger(logging.getLogger(__name__))


def api_call(method, endpoint, parameters=None, json=None, headers=None):
    url = app.config['RAS_FRONTSTAGE_API_SERVICE'] + endpoint
    if parameters:
        url = '{}?'.format(url)
        for key, value in parameters.items():
            parameter_string = '{}={}&'.format(key, value)
            url = url + parameter_string
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=json)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=json)
        else:
            logger.error('Invalid request method', method=str(method), url=url)
            raise InvalidRequestMethod(method, url)
    except ConnectTimeout as e:
        logger.error('Connection to remote server timed out', method=method, url=url, exception=str(e))
        raise FailedRequest(method, url, e)

    except ConnectionError as e:
        logger.error('Failed to connect to external service', method=method, url=url, exception=str(e))
        raise FailedRequest(method, url, e)

    return response
