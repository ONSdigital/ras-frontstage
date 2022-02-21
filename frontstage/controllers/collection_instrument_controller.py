import logging
import os

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
from frontstage.exceptions.exceptions import ApiError, CiUploadError, CiUploadErrorNew

logger = wrap_logger(logging.getLogger(__name__))

INVALID_UPLOAD = "The upload must have valid case_id and a file attached"
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
        raise ApiError(logger, response)

    logger.info("Successfully downloaded collection instrument")

    headers = response.headers
    acao = app.config["ACCESS_CONTROL_ALLOW_ORIGIN"]
    bound_logger.debug(f"Setting Access-Control-Allow-Origin header to {acao}")
    headers["Access-Control-Allow-Origin"] = acao
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


def upload_collection_instrument_new(file, case: dict, business_party: dict, party_id: str, survey: dict):
    """

    :param file: A dict containing the
    :param case: The case that relates to the upload
    :param business_party: The record of the business the upload is for
    :param party_id: The party id of the respondent that uploaded the instrument
    :param survey:  A dict containing information about the survey
    :raises CiUploadErrorNew: Raised on a validation error
    """
    case_id = case["id"]
    logger.info("Attempting to upload collection instrument", case_id=case_id, party_id=party_id)
    if case_id and file and file.filename:
        file_name, file_extension = os.path.splitext(secure_filename(file.filename))
        gcp_survey_response = GcpSurveyResponse(app.config)
        is_valid_file, msg = gcp_survey_response.is_valid_file(file_name, file_extension)

        if not is_valid_file:
            ci_post_case_event(case_id, party_id, "UNSUCCESSFUL_RESPONSE_UPLOAD")
            raise CiUploadErrorNew(msg)

        survey_ref = survey.get("surveyRef")
        file_name = gcp_survey_response.create_file_name_for_upload(case, business_party, file_extension, survey_ref)

        if not file_name:
            raise CiUploadErrorNew(MISSING_DATA)
        try:
            file_contents = file.read()
            gcp_survey_response.add_survey_response(case, file_contents, file_name, survey_ref)
            ci_post_case_event(case_id, party_id, "SUCCESSFUL_RESPONSE_UPLOAD")
            logger.info("Successfully uploaded collection instrument", case_id=case_id, party_id=party_id)
        except FileTooSmallError:
            ci_post_case_event(case_id, party_id, "UNSUCCESSFUL_RESPONSE_UPLOAD")
            raise CiUploadErrorNew(FILE_TOO_SMALL)
        except SurveyResponseError:
            ci_post_case_event(case_id, party_id, "UNSUCCESSFUL_RESPONSE_UPLOAD")
            raise CiUploadErrorNew(UPLOAD_UNSUCCESSFUL)
    else:
        logger.info("Either case_id, file or file attributes are missing.")
        ci_post_case_event(case_id, party_id, "UNSUCCESSFUL_RESPONSE_UPLOAD")
        raise CiUploadErrorNew(INVALID_UPLOAD)


def ci_post_case_event(case_id, party_id, category):
    # Post relevant upload case event
    case_controller.post_case_event(
        case_id,
        party_id=party_id,
        category=category,
        description=f"Survey response for case {case_id} uploaded by {party_id}",
    )


def upload_collection_instrument(upload_file, case_id, party_id):
    logger.info("Attempting to upload collection instrument", case_id=case_id, party_id=party_id)

    url = f"{app.config['COLLECTION_INSTRUMENT_URL']}/survey_response-api/v1/survey_responses/{case_id}"
    response = requests.post(url, auth=app.config["BASIC_AUTH"], files=upload_file)

    # Post relevant upload case event
    category = "SUCCESSFUL_RESPONSE_UPLOAD" if response.ok else "UNSUCCESSFUL_RESPONSE_UPLOAD"
    case_controller.post_case_event(
        case_id,
        party_id=party_id,
        category=category,
        description=f"Survey response for case {case_id} uploaded by {party_id}",
    )

    if response.status_code == 400:
        raise CiUploadError(logger, response, case_id=case_id, error_message=response.text, party_id=party_id)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to upload collection instrument", case_id=case_id, party_id=party_id)
        raise ApiError(logger, response)

    logger.info("Successfully uploaded collection instrument", case_id=case_id, party_id=party_id)
