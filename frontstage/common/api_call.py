import logging

import requests
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import InvalidRequestMethod


logger = wrap_logger(logging.getLogger(__name__))


def api_call(method, endpoint, parameters=None, json=None, files=None, headers=None, url=None, auth=app.config['BASIC_AUTH']):

    if not url:
        url = app.config['RAS_FRONTSTAGE_API_SERVICE'] + endpoint

    logger.debug('Calling frontstage api', method=method, url=url)
    if method == 'GET':
        response = requests.get(url, headers=headers,
                                auth=auth, params=parameters)
    elif method == 'POST':
        response = requests.post(url, headers=headers, json=json, files=files,
                                 auth=auth, params=parameters)
    elif method == 'PUT':
        response = requests.put(url, headers=headers, json=json,
                                auth=auth, params=parameters)
    else:
        logger.error('Invalid request method', method=method, url=url)
        raise InvalidRequestMethod(method, url)

    logger.debug('Frontstage-api response', method=method, url=url, status=response.status_code)
    return response
