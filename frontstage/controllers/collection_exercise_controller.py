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
        log_level = logger.warning if response.status_code == 404 else logger.exception
        log_level('Failed to retrieve collection exercise',
                  collection_exercise_id=collection_exercise_id,
                  status=response.status_code)
        raise ApiError(response)

    logger.debug('Successfully retrieved collection exercise', collection_exercise_id=collection_exercise_id)
    return response.json()


def get_collection_exercise_event(collection_exercise_id, tag):
    logger.debug('Retrieving collection exercise event', collection_exercise_id=collection_exercise_id, tag=tag)
    url = f"{app.config['COLLECTION_EXERCISE_URL']}/collectionexercises/{collection_exercise_id}/events/{tag}"

    response = requests.get(url, auth=app.config['COLLECTION_EXERCISE_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        log_level = logger.warning if response.status_code == 404 else logger.exception
        log_level('Failed to retrieve collection exercise event',
                  collection_exercise_id=collection_exercise_id,
                  status=response.status_code,
                  tag=tag)
        raise ApiError(response)

    logger.debug('Successfully retrieved collection exercise event', collection_exercise_id=collection_exercise_id, tag=tag)
    return response.json()
