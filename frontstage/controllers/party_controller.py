import logging

from flask import current_app as app
import requests
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError


logger = wrap_logger(logging.getLogger(__name__))


def get_party_by_business_id(party_id, collection_exercise_id=None):
    logger.debug('Attempting to retrieve party by business',
                 collection_exercise_id=collection_exercise_id,
                 party_id=party_id)

    url = f"{app.config['PARTY_URL']}/party-api/v1/businesses/id/{party_id}"
    if collection_exercise_id:
        url += f"?collection_exercise_id={collection_exercise_id}&verbose=True"
    response = requests.get(url, auth=app.config['PARTY_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        log_level = logger.warning if response.status_code == 404 else logger.exception
        log_level('Failed to retrieve party',
                  collection_exercise_id=collection_exercise_id,
                  party_id=party_id)
        raise ApiError(response)

    logger.debug('Successfully retrieved party by business',
                 collection_exercise_id=collection_exercise_id,
                 party_id=party_id)
    return response.json()
