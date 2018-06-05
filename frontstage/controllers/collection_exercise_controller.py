import logging

import requests
from flask import current_app as app
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError


logger = wrap_logger(logging.getLogger(__name__))


def get_collection_exercise(collection_exercise_id):
    logger.debug('Attempting to retrieve collection exercise', collection_exercise_id=collection_exercise_id)
    url = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise_id}"

    response = requests.get(url, auth=app.config['COLLECTION_EXERCISE_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       collection_exercise_id=collection_exercise_id,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to retrieve collection exercise')

    logger.debug('Successfully retrieved collection exercise', collection_exercise_id=collection_exercise_id)
    return response.json()


def get_collection_exercise_event(collection_exercise_id, tag):
    logger.debug('Retrieving collection exercise event', collection_exercise_id=collection_exercise_id, tag=tag)
    url = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise_id}/events/{tag}"

    response = requests.get(url, auth=app.config['COLLECTION_EXERCISE_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       collection_exercise_id=collection_exercise_id,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to retrieve collection exercise event',
                       tag=tag)

    logger.debug('Successfully retrieved collection exercise event', collection_exercise_id=collection_exercise_id, tag=tag)
    return response.json()


def get_collection_exercise_events(collection_exercise_id):
    logger.debug('Attempting to retrieve collection exercise events', collection_exercise_id=collection_exercise_id)
    url = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise_id}/events"

    response = requests.get(url, auth=app.config['COLLECTION_EXERCISE_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       collection_exercise_id=collection_exercise_id,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to retrieve collection exercise events')

    logger.debug('Successfully retrieved collection exercise events', collection_exercise_id=collection_exercise_id)
    return response.json()
