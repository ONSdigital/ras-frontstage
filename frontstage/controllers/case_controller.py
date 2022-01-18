import logging

import requests
from flask import abort
from flask import current_app as app
from structlog import wrap_logger

from frontstage.common.encrypter import Encrypter
from frontstage.common.eq_payload import EqPayload
from frontstage.controllers import (
    collection_exercise_controller,
    collection_instrument_controller,
    party_controller,
    survey_controller,
)
from frontstage.exceptions.exceptions import (
    ApiError,
    InvalidCaseCategory,
    NoSurveyPermission,
)

logger = wrap_logger(logging.getLogger(__name__))


def calculate_case_status(case_group_status, collection_instrument_type):
    """
    Given a case group status and instrument type, this will generate user readable text to describe the status.

    :param case_group_status: Status of the case group
    :type case_group_status: str
    :param collection_instrument_type: The type of collection instrument.  Either EQ or SEFT
    :type collection_instrument_type: str
    :return: A user readable description of the status.
    """
    logger.info(
        "Getting the status of caseGroup",
        case_group_status=case_group_status,
        collection_instrument_type=collection_instrument_type,
    )

    status = "Not started"

    if case_group_status == "COMPLETE":
        status = "Complete"
    elif case_group_status == "COMPLETEDBYPHONE":
        status = "Completed by phone"
    elif case_group_status == "NOLONGERREQUIRED":
        status = "No longer required"
    elif case_group_status == "INPROGRESS" and collection_instrument_type == "EQ":
        status = "In progress"
    elif case_group_status == "INPROGRESS" and collection_instrument_type == "SEFT":
        status = "Downloaded"

    logger.info("Retrieved the status of case", collection_instrument_type=collection_instrument_type, status=status)
    return status


def get_case_by_case_id(case_id):
    logger.info("Attempting to retrieve case by case id", case_id=case_id)

    url = f"{app.config['CASE_URL']}/cases/{case_id}"
    response = requests.get(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to retrieve case by case id", case_id=case_id)
        raise ApiError(logger, response)

    logger.info("Successfully retrieved case by case id", case_id=case_id)
    return response.json()


def get_case_by_enrolment_code(enrolment_code):
    logger.info("Attempting to retrieve case by enrolment code")

    url = f"{app.config['CASE_URL']}/cases/iac/{enrolment_code}"
    response = requests.get(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to retrieve case by enrolment code")
        raise ApiError(logger, response)

    logger.info("Successfully retrieved case by enrolment code")
    return response.json()


def get_case_categories():
    logger.info("Attempting to retrieve case categories")

    url = f"{app.config['CASE_URL']}/categories"
    response = requests.get(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to get case categories")
        raise ApiError(logger, response)

    logger.info("Successfully retrieved case categories")
    return response.json()


def get_case_data(case_id, party_id, business_party_id, survey_short_name):
    logger.info("Attempting to retrieve detailed case data", case_id=case_id, party_id=party_id)

    # Check if respondent has permission to see case data
    case = get_case_by_case_id(case_id)
    survey = survey_controller.get_survey_by_short_name(survey_short_name)
    if not party_controller.is_respondent_enrolled(party_id, business_party_id, survey):
        raise NoSurveyPermission(party_id, case_id)

    case_data = {
        "collection_exercise": collection_exercise_controller.get_collection_exercise(
            case["caseGroup"]["collectionExerciseId"]
        ),
        "collection_instrument": collection_instrument_controller.get_collection_instrument(
            case["collectionInstrumentId"], app.config["COLLECTION_INSTRUMENT_URL"], app.config["BASIC_AUTH"]
        ),
        "survey": survey,
        "business_party": party_controller.get_party_by_business_id(
            business_party_id, app.config["PARTY_URL"], app.config["BASIC_AUTH"]
        ),
    }

    logger.info("Successfully retrieved all data relating to case", case_id=case_id, party_id=party_id)
    return case_data


def get_cases_by_party_id(party_id, case_url, case_auth, case_events=False, iac=True):
    logger.info("Attempting to retrieve cases by party id", party_id=party_id)

    url = f"{case_url}/cases/partyid/{party_id}"
    if case_events:
        url = f"{url}?caseevents=true"
    if not iac:
        if case_events:
            url = f"{url}&"
        else:
            url = f"{url}?"
        url = f"{url}iac=false"
    response = requests.get(url, auth=case_auth)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to retrieve cases by party id", party_id=party_id)
        raise ApiError(logger, response)

    logger.info("Successfully retrieved cases by party id", party_id=party_id)
    return response.json()


def get_eq_url(version, case, collection_exercise, party_id, business_party_id, survey_short_name):
    case_id = case["id"]
    logger.info("Attempting to generate EQ URL", case_id=case_id, party_id=party_id, version=version)

    if version not in ["v2", "v3"]:
        # EQ collection exercises created before the concept of versions might have a null value for the version.
        # If this is the case, we can safely assume it's v2 as that was the only one availible at the time.
        if version is None:
            logger.info("EQ version not set, assuming v2", case_id=case_id, party_id=party_id, version=version)
            version = "v2"
        else:
            raise ValueError(f"The eq version [{version}] is not supported")

    if case["caseGroup"]["caseGroupStatus"] in ("COMPLETE", "COMPLETEDBYPHONE", "NOLONGERREQUIRED"):
        logger.info("The case group status is complete, opening an EQ is forbidden", case_id=case_id, party_id=party_id)
        abort(403)

    survey = survey_controller.get_survey_by_short_name(survey_short_name)
    if not party_controller.is_respondent_enrolled(party_id, business_party_id, survey):
        raise NoSurveyPermission(party_id, case_id)

    payload = EqPayload().create_payload(case, collection_exercise, party_id, business_party_id, survey)

    json_secret_keys = app.config["JSON_SECRET_KEYS"]
    encrypter = Encrypter(json_secret_keys)

    if version == "v2":
        token = encrypter.encrypt(payload, "eq")
        eq_url = app.config["EQ_URL"] + token
    elif version == "v3":
        token = encrypter.encrypt(payload, "eq_v3")
        eq_url = app.config["EQ_V3_URL"] + token

    category = "EQ_LAUNCH"
    ci_id = case["collectionInstrumentId"]
    post_case_event(
        case_id,
        party_id=party_id,
        category=category,
        description=f"Instrument {ci_id} launched by {party_id} for case {case_id}",
    )

    logger.info(
        "Successfully generated EQ URL",
        case_id=case_id,
        ci_id=ci_id,
        party_id=party_id,
        business_party_id=business_party_id,
        survey_short_name=survey_short_name,
        tx_id=payload["tx_id"],
        version=version,
    )
    return eq_url


def post_case_event(case_id, party_id, category, description):
    logger.info("Posting case event", case_id=case_id)

    validate_case_category(category)
    url = f"{app.config['CASE_URL']}/cases/{case_id}/events"
    message = {
        "description": description,
        "category": category,
        "metadata": {"partyId": party_id},
        "createdBy": "RAS_FRONTSTAGE",
    }
    response = requests.post(url, auth=app.config["BASIC_AUTH"], json=message)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to post case event", case_id=case_id)
        raise ApiError(logger, response)

    logger.info("Successfully posted case event", case_id=case_id)


def validate_case_category(category):
    logger.info("Validating case category", category=category)

    categories = get_case_categories()
    category_names = [cat["name"] for cat in categories]
    if category not in category_names:
        raise InvalidCaseCategory(category)

    logger.info("Successfully validated case category", category=category)


def get_cases_for_list_type_by_party_id(party_id, case_url, case_auth, list_type="todo"):
    logger.info("Get cases for party for list", party_id=party_id, list_type=list_type)

    cases = get_cases_by_party_id(party_id, case_url, case_auth, iac=False)
    history_statuses = ["COMPLETE", "COMPLETEDBYPHONE", "NOLONGERREQUIRED"]
    if list_type == "history":
        filtered_cases = [
            business_case
            for business_case in cases
            if business_case["caseGroup"]["caseGroupStatus"] in history_statuses
        ]
    else:
        filtered_cases = [
            business_case
            for business_case in cases
            if business_case["caseGroup"]["caseGroupStatus"] not in history_statuses
        ]

    logger.info("Successfully retrieved cases for party survey list", party_id=party_id, list_type=list_type)
    return filtered_cases
