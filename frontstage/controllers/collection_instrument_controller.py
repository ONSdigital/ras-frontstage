import logging

import requests
from flask import current_app as app
from structlog import wrap_logger

from frontstage.controllers import case_controller
from frontstage.exceptions.exceptions import ApiError, CiUploadError


logger = wrap_logger(logging.getLogger(__name__))


def download_collection_instrument(collection_instrument_id, case_id, party_id):
    logger.debug('Attempting to download collection instrument',
                 collection_instrument_id=collection_instrument_id,
                 party_id=party_id)

    url = f"{app.config['COLLECTION_INSTRUMENT_URL']}/collection-instrument-api/1.0.2/download/{collection_instrument_id}"
    response = requests.get(url, auth=app.config['COLLECTION_INSTRUMENT_AUTH'])

    # Post relevant download case event
    category = 'COLLECTION_INSTRUMENT_DOWNLOADED' if response.ok else 'COLLECTION_INSTRUMENT_ERROR'
    case_controller.post_case_event(case_id,
                                    party_id=party_id,
                                    category=category,
                                    description=f'Instrument {collection_instrument_id} downloaded by {party_id} for case {case_id}')

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       collection_instrument_id=collection_instrument_id,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to download collection instrument',
                       party_id=party_id)

    logger.debug('Successfully downloaded collection instrument',
                 collection_instrument_id=collection_instrument_id,
                 party_id=party_id)
    return response.content, response.headers.items()


def get_collection_instrument(collection_instrument_id):
    logger.debug('Attempting to retrieve collection instrument',
                 collection_instrument_id=collection_instrument_id)

    url = f"{app.config['COLLECTION_INSTRUMENT_URL']}/collection-instrument-api/1.0.2/collectioninstrument/id/{collection_instrument_id}"
    response = requests.get(url, auth=app.config['COLLECTION_INSTRUMENT_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       collection_instrument_id=collection_instrument_id,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to get collection instrument')

    logger.debug('Successfully retrieved collection instrument',
                 collection_instrument_id=collection_instrument_id)
    return response.json()


def get_collection_instrument_with_config(config, collection_instrument_id):
    logger.debug('Attempting to retrieve collection instrument',
                 collection_instrument_id=collection_instrument_id)

    url = f"{config['COLLECTION_INSTRUMENT_URL']}/collection-instrument-api/1.0.2/collectioninstrument/id/{collection_instrument_id}"
    response = requests.get(url, auth=config['COLLECTION_INSTRUMENT_AUTH'])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       collection_instrument_id=collection_instrument_id,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to get collection instrument')

    logger.debug('Successfully retrieved collection instrument',
                 collection_instrument_id=collection_instrument_id)
    return response.json()


def upload_collection_instrument(upload_file, case_id, party_id):
    logger.debug('Attempting to upload collection instrument', case_id=case_id, party_id=party_id)

    url = f"{app.config['COLLECTION_INSTRUMENT_URL']}/survey_response-api/v1/survey_responses/{case_id}"
    response = requests.post(url, auth=app.config['COLLECTION_INSTRUMENT_AUTH'], files=upload_file)

    # Post relevant upload case event
    category = 'SUCCESSFUL_RESPONSE_UPLOAD' if response.ok else 'UNSUCCESSFUL_RESPONSE_UPLOAD'
    case_controller.post_case_event(case_id,
                                    party_id=party_id,
                                    category=category,
                                    description=f'Survey response for case {case_id} uploaded by {party_id}')

    if response.status_code == 400:
        raise CiUploadError(logger, response, case_id=case_id, error_message=response.text, party_id=party_id)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response,
                       case_id=case_id,
                       log_level='warning' if response.status_code == 404 else 'exception',
                       message='Failed to upload collection instrument',
                       party_id=party_id)

    logger.debug('Successfully uploaded collection instrument', case_id=case_id, party_id=party_id)
