import logging

from flask import current_app as app
from structlog import wrap_logger

from frontstage.common.request_handler import request_handler
from frontstage.exceptions.exceptions import ApiError


logger = wrap_logger(logging.getLogger(__name__))


def get_collection_exercise(collection_exercise_id):
    logger.debug('Retrieving collection exercise', collection_exercise_id=collection_exercise_id)
    url = f"{app.config['RM_COLLECTION_EXERCISE_SERVICE']}/collectionexercises/{collection_exercise_id}"
    response = request_handler('GET', url, auth=app.config['BASIC_AUTH'])

    if response.status_code != 200:
        raise ApiError(url=url, status_code=response.status_code,
                       description='Failed to retrieve collection exercise',
                       collection_exercise_id=collection_exercise_id)

    logger.debug('Successfully retrieved collection exercise', collection_exercise_id=collection_exercise_id)
    return response.json()


def get_collection_exercise_events(collection_exercise_id):
    logger.debug('Retrieving collection exercise events', collection_exercise_id=collection_exercise_id)
    url = f"{app.config['RM_COLLECTION_EXERCISE_SERVICE']}/collectionexercises/{collection_exercise_id}/events"

    response = request_handler('GET', url, auth=app.config['BASIC_AUTH'])

    if response.status_code != 200:
        raise ApiError(url=url, status_code=response.status_code,
                       description='Failed to retrieve collection exercise events',
                       collection_exercise_id=collection_exercise_id)

    logger.debug('Successfully retrieved collection exercise events', collection_exercise_id=collection_exercise_id)
    return response.json()


def get_collection_exercise_event(collection_exercise_id, tag):
    logger.debug('Retrieving collection exercise event', collection_exercise_id=collection_exercise_id, tag=tag)
    url = f"{app.config['RM_COLLECTION_EXERCISE_SERVICE']}/collectionexercises/{collection_exercise_id}/events/{tag}"

    response = request_handler('GET', url, auth=app.config['BASIC_AUTH'])

    if response.status_code != 200:
        raise ApiError(url=url, status_code=response.status_code,
                       description='Failed to retrieve collection exercise event',
                       collection_exercise_id=collection_exercise_id, tag=tag)

    logger.debug('Successfully retrieved collection exercise event', collection_exercise_id=collection_exercise_id, tag=tag)
    return response.json()
