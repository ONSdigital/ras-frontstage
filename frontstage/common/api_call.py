import logging

import requests
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import InvalidRequestMethod


logger = wrap_logger(logging.getLogger(__name__))


def api_call(method, endpoint, parameters=None, json=None, headers=None):
    url = app.config['RAS_FRONTSTAGE_API_SERVICE'] + endpoint
    if parameters:
        url = '{}?'.format(url)
        for key, value in parameters.items():
            parameter_string = '{}={}&'.format(key, value)
            url = url + parameter_string

    if method == 'GET':
        response = requests.get(url, headers=headers, auth=app.config['BASIC_AUTH'])
    elif method == 'POST':
        response = requests.post(url, headers=headers, json=json, auth=app.config['BASIC_AUTH'])
    elif method == 'PUT':
        response = requests.put(url, headers=headers, json=json, auth=app.config['BASIC_AUTH'])
    else:
        logger.error('Invalid request method', method=str(method), url=url)
        raise InvalidRequestMethod(method, url)

    return response
