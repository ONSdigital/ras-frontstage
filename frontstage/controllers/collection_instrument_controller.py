import logging
import os
from functools import lru_cache

import requests
from flask import current_app as app
from structlog import wrap_logger
from werkzeug.utils import secure_filename

from frontstage.controllers import case_controller
from frontstage.controllers.gcp_survey_response import (
    FileTooSmallError,
    GcpSurveyResponse,
    SurveyResponseError,
)
from frontstage.exceptions.exceptions import ApiError, CiUploadError

logger = wrap_logger(logging.getLogger(__name__))

INVALID_UPLOAD = "The upload must have a file attached"
MISSING_DATA = "Data needed to create the file name is missing"
UPLOAD_SUCCESSFUL = "Upload successful"
UPLOAD_UNSUCCESSFUL = "Upload failed"
FILE_TOO_SMALL = "File too small"


def download_collection_instrument(collection_instrument_id, case_id, party_id):
    """
    Downloads the collection instrument and updates the case with the record that the instrument has been downloaded.

    :param collection_instrument_id: UUID of the collection instrument
    :param case_id: UUID of the case
    :param party_id: UUID of the party
    :return: A tuple containing the collection instrument and the headers
    """
    bound_logger = logger.bind(collection_instrument_id=collection_instrument_id, party_id=party_id, case_id=case_id)
    bound_logger.info("Attempting to download collection instrument")

    url = (
        f"{app.config['COLLECTION_INSTRUMENT_URL']}/collection-instrument-api/1.0.2/download/{collection_instrument_id}"
    )
    response = requests.get(url, auth=app.config["BASIC_AUTH"])

    # Post relevant download case event
    category = "COLLECTION_INSTRUMENT_DOWNLOADED" if response.ok else "COLLECTION_INSTRUMENT_ERROR"
    case_controller.post_case_event(
        case_id,
        party_id=party_id,
        category=category,
        description=f"Instrument {collection_instrument_id} downloaded by {party_id} for case {case_id}",
    )

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        bound_logger.error("Failed to download collection instrument")
        bound_logger.unbind("collection_instrument_id", "party_id", "case_id")
        raise ApiError(logger, response)

    bound_logger.info("Successfully downloaded collection instrument")

    headers = response.headers
    acao = app.config["ACCESS_CONTROL_ALLOW_ORIGIN"]
    bound_logger.debug(f"Setting Access-Control-Allow-Origin header to {acao}")
    headers["Access-Control-Allow-Origin"] = acao
    bound_logger.unbind("collection_instrument_id", "party_id", "case_id")
    return response.content, headers.items()


def get_collection_instrument(collection_instrument_id, collection_instrument_url, collection_instrument_auth):
    logger.info("Attempting to retrieve collection instrument", collection_instrument_id=collection_instrument_id)

    url = f"{collection_instrument_url}/collection-instrument-api/1.0.2/{collection_instrument_id}"
    response = requests.get(url, auth=collection_instrument_auth)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to get collection instrument", collection_instrument_id=collection_instrument_id)
        raise ApiError(logger, response)

    logger.info("Successfully retrieved collection instrument", collection_instrument_id=collection_instrument_id)
    return response.json()


@lru_cache
def get_registry_instrument(exercise_id, form_type) -> dict or None:
    url = (
        f"{app.config["COLLECTION_INSTRUMENT_URL"]}/collection-instrument-api/1.0.2/registry-instrument/exercise-id/"
        f"{exercise_id}/formtype/{form_type}"
    )
    response = requests.get(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error(
            "No registry instrument found for exercise_id and form_type",
            collection_exercise_id=exercise_id,
            form_type=form_type,
        )
        return None

    logger.info(
        "Successfully retrieved registry instrument by exercise_id and form_type",
        collection_exercise_id=exercise_id,
        form_type=form_type,
    )
    return response.json()


def upload_collection_instrument(file, case: dict, business_party: dict, party_id: str, survey: dict):
    """

    :param file: A dict containing the
    :param case: The case that relates to the upload
    :param business_party: The record of the business the upload is for
    :param party_id: The party id of the respondent that uploaded the instrument
    :param survey: A dict containing information about the survey
    :raises CiUploadError: Raised on a validation error
    """
    case_id = case["id"]
    logger.info("Attempting to upload collection instrument", case_id=case_id, party_id=party_id)
    if case_id and file and file.filename:
        file_name, file_extension = os.path.splitext(secure_filename(file.filename))
        gcp_survey_response = GcpSurveyResponse(app.config)
        is_valid_file, msg = gcp_survey_response.is_valid_file(file_name, file_extension)

        if not is_valid_file:
            ci_post_case_event(case_id, party_id, "UNSUCCESSFUL_RESPONSE_UPLOAD")
            return msg

        survey_ref = survey.get("surveyRef")
        file_name = gcp_survey_response.create_file_name_for_upload(case, business_party, file_extension, survey_ref)

        if not file_name:
            raise CiUploadError(MISSING_DATA)
        try:
            file_contents = file.read()
            gcp_survey_response.upload_seft_survey_response(case, file_contents, file_name, survey_ref)
            ci_post_case_event(case_id, party_id, "SUCCESSFUL_RESPONSE_UPLOAD")
            logger.info("Successfully uploaded collection instrument", case_id=case_id, party_id=party_id)
            return None
        except FileTooSmallError:
            ci_post_case_event(case_id, party_id, "UNSUCCESSFUL_RESPONSE_UPLOAD")
            return FILE_TOO_SMALL
        except SurveyResponseError:
            ci_post_case_event(case_id, party_id, "UNSUCCESSFUL_RESPONSE_UPLOAD")
            raise CiUploadError(UPLOAD_UNSUCCESSFUL)
    else:
        logger.info(INVALID_UPLOAD, case_id=case_id, party_id=party_id)
        ci_post_case_event(case_id, party_id, "UNSUCCESSFUL_RESPONSE_UPLOAD")
        return INVALID_UPLOAD


def ci_post_case_event(case_id, party_id, category):
    # Post relevant upload case event
    case_controller.post_case_event(
        case_id,
        party_id=party_id,
        category=category,
        description=f"Survey response for case {case_id} uploaded by {party_id}",
    )
