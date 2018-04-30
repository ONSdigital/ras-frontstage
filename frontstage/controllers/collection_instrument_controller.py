import logging

from flask import current_app as app
import requests
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError


logger = wrap_logger(logging.getLogger(__name__))


def get_collection_instrument(collection_instrument_id):
    logger.debug('Attempting to retrieve collection instrument',
                 collection_instrument_id=collection_instrument_id)
    url = f"{app.config['COLLECTION_INSTRUMENT_SERVICE_URL']}/collection-instrument-api/1.0.2/collectioninstrument/id/{collection_instrument_id}"
    response = requests.get(url, auth=app.config['BASIC_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.exception('Failed to get collection instrument', collection_instrument_id=collection_instrument_id)
        raise ApiError(response)

    logger.debug('Successfully retrieved collection instrument',
                 collection_instrument_id=collection_instrument_id)
    return response.json()
