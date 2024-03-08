import json
import logging

import requests
from flask import current_app as app
from structlog import wrap_logger
from werkzeug.exceptions import NotFound

from frontstage.common.thread_wrapper import ThreadWrapper
from frontstage.common.utilities import obfuscate_email
from frontstage.common.verification import decode_email_token
from frontstage.controllers import case_controller, survey_controller
from frontstage.exceptions.exceptions import ApiError, UserDoesNotExist

CLOSED_STATE = ["COMPLETE", "COMPLETEDBYPHONE", "NOLONGERREQUIRED"]

logger = wrap_logger(logging.getLogger(__name__))


def get_respondent_party_by_id(party_id: str) -> dict:
    logger.info("Retrieving party from party service by id", party_id=party_id)

    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/id/{party_id}"
    response = requests.get(url, auth=app.config["BASIC_AUTH"])

    if response.status_code == 404:
        return

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to find respondent", party_id=party_id)
        raise ApiError(logger, response)

    logger.info("Successfully retrieved party details", party_id=party_id)
    return response.json()


def add_survey(party_id, enrolment_code):
    logger.info("Attempting to add a survey", party_id=party_id)

    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/add_survey"
    request_json = {"party_id": party_id, "enrolment_code": enrolment_code}
    response = requests.post(url, auth=app.config["BASIC_AUTH"], json=request_json)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to add a survey", party_id=party_id, enrolment_code=enrolment_code)
        raise ApiError(logger, response)

    logger.info("Successfully added a survey", party_id=party_id, enrolment_code=enrolment_code)


def change_password(email, password):
    bound_logger = logger.bind(email=obfuscate_email(email))
    bound_logger.info("Attempting to change password through the party service")

    data = {"email_address": email, "new_password": password}
    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/change_password"
    response = requests.put(url, auth=app.config["BASIC_AUTH"], json=data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        bound_logger.error("Failed to send change password request to party service")
        raise ApiError(logger, response)

    bound_logger.info("Successfully changed password through the party service")


def create_account(registration_data: dict) -> None:
    obfuscated_email = obfuscate_email(registration_data["emailAddress"])
    enrolment_code = registration_data["enrolmentCode"]
    logger.info("Attempting to create account", email=obfuscated_email, enrolment_code=enrolment_code)

    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents"
    registration_data["status"] = "CREATED"
    response = requests.post(url, auth=app.config["BASIC_AUTH"], json=registration_data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 409:
            logger.info("Email has already been used", email=obfuscated_email, enrolment_code=enrolment_code)
        else:
            logger.error("Failed to create account", email=obfuscated_email, enrolment_code=enrolment_code)
        raise ApiError(logger, response, message=response.json())

    logger.info("Successfully created account", email=obfuscated_email, enrolment_code=enrolment_code)


def update_account(respondent_data):
    logger.info("Attempting to update account", party_id=respondent_data["id"])

    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/id/{respondent_data['id']}"
    response = requests.put(url, auth=app.config["BASIC_AUTH"], json=respondent_data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to update account", party_id=respondent_data["id"])
        raise ApiError(logger, response)

    logger.info("Successfully updated account", party_id=respondent_data["id"])


def get_party_by_business_id(party_id, party_url, party_auth, collection_exercise_id=None, verbose=True):
    logger.info(
        "Attempting to retrieve party by business", party_id=party_id, collection_exercise_id=collection_exercise_id
    )

    url = f"{party_url}/party-api/v1/businesses/id/{party_id}"
    params = {}
    if collection_exercise_id:
        params["collection_exercise_id"] = collection_exercise_id
    if verbose:
        params["verbose"] = True
    response = requests.get(url, params=params, auth=party_auth)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error(
            "Failed to retrieve party by business", party_id=party_id, collection_exercise_id=collection_exercise_id
        )
        raise ApiError(logger, response)

    logger.info(
        "Successfully retrieved party by business", party_id=party_id, collection_exercise_id=collection_exercise_id
    )
    return response.json()


"""
This import had to be moved as redis_cache calls the get_party_by_business_id method which needs to be
initialised before being used
"""
from frontstage.common.redis_cache import RedisCache  # NOQA: E402


def get_respondent_by_email(email):
    bound_logger = logger.bind(email=obfuscate_email(email))
    bound_logger.info("Attempting to find respondent party by email")

    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/email"
    response = requests.get(url, json={"email": email}, auth=app.config["BASIC_AUTH"])

    if response.status_code == 404:
        bound_logger.info("Failed to retrieve party by email")
        return

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        bound_logger.error("Error retrieving respondent by email")
        raise ApiError(logger, response)

    bound_logger.info("Successfully retrieved respondent by email")
    return response.json()


def resend_verification_email(party_id):
    logger.info("Re-sending verification email", party_id=party_id)
    url = f'{app.config["PARTY_URL"]}/party-api/v1/resend-verification-email/{party_id}'
    response = requests.post(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.exception("Re-sending of verification email failed", party_id=party_id)
        raise ApiError(logger, response)
    logger.info("Successfully re-sent verification email", party_id=party_id)


def resend_verification_email_expired_token(token):
    logger.info("Re-sending verification email", token=token)
    url = f'{app.config["PARTY_URL"]}/party-api/v1/resend-verification-email-expired-token/{token}'
    response = requests.post(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Re-sending of verification email for expired token failed")
        raise ApiError(logger, response)
    logger.info("Successfully re-sent verification email", token=token)


def resend_account_email_change_expired_token(token):
    logger.info("Re-sending account email change verification email", token=token)
    url = f'{app.config["PARTY_URL"]}/party-api/v1/resend-account-email-change-expired-token/{token}'
    response = requests.post(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Re-sending of verification email for expired token failed", token=token)
        raise ApiError(logger, response)
    logger.info("Successfully re-sent verification email", token=token)


def reset_password_request(username):
    bound_logger = logger.bind(email=obfuscate_email(username))
    bound_logger.info("Attempting to send reset password request to party service")

    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/request_password_change"
    data = {"email_address": username}
    response = requests.post(url, auth=app.config["BASIC_AUTH"], json=data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            raise UserDoesNotExist("User does not exist in party service")
        bound_logger.error("Failed to send reset password request to party service")
        raise ApiError(logger, response)

    bound_logger.info("Successfully sent reset password request to party service")


def resend_password_email_expired_token(token):
    logger.info("Re-sending password email", token=token)
    url = f'{app.config["PARTY_URL"]}/party-api/v1/resend-password-email-expired-token/{token}'
    response = requests.post(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Re-sending of password email for expired token failed")
        raise ApiError(logger, response)
    logger.info("Sucessfully re-sent password email", token=token)


def verify_email(token):
    logger.info("Attempting to verify email address", token=token)

    url = f"{app.config['PARTY_URL']}/party-api/v1/emailverification/{token}"
    response = requests.put(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to verify email", token=token)
        raise ApiError(logger, response)

    logger.info("Successfully verified email address", token=token)


def verify_token(token):
    logger.info("Attempting to verify token with party service", token=token)

    url = f"{app.config['PARTY_URL']}/party-api/v1/tokens/verify/{token}"
    response = requests.get(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to verify token", token=token)
        raise ApiError(logger, response)

    logger.info("Successfully verified token", token=token)


def verify_pending_survey_token(token):
    """
    Gives call to party service to verify share/transfer survey token
    """
    logger.info("Attempting to verify share/transfer survey token with party service", token=token)

    url = f"{app.config['PARTY_URL']}/party-api/v1/pending-survey/verification/{token}"
    response = requests.get(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to verify share/transfer survey token", token=token)
        raise ApiError(logger, response)

    logger.info("Successfully verified token", token=token)
    return response


def confirm_pending_survey(batch_number):
    """
    gives call to party service to confirm pending share/transfer survey
    """
    logger.info("Attempting to confirm share/transfer survey with party service", batch_number=batch_number)

    url = f"{app.config['PARTY_URL']}/party-api/v1/pending-survey/confirm-pending-surveys/{batch_number}"
    response = requests.post(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to confirm share/transfer survey with batch number", batch_number=batch_number)
        raise ApiError(logger, response)

    logger.info("Successfully confirmed share/transfer survey", batch_number=batch_number)
    return response


def get_respondent_enrolments(respondent: dict):
    """
    Returns a generator containing all the business_id and survey_id for all the active enrolments for the
    respondent.

    :param respondent: A dict containing respondent data
    """
    if "associations" in respondent:
        for association in respondent["associations"]:
            for enrolment in association["enrolments"]:
                if enrolment["enrolmentStatus"] == "ENABLED":
                    yield {"business_id": association["partyId"], "survey_id": enrolment["surveyId"]}


def get_respondent_enrolments_for_started_collex(enrolment_data, collection_exercises):
    """This will only filter out enrolments for surveys that have 0 live collection exercises.

    Needed because enrolment_data includes not started enrolments ,
    but cache_collex only contains started collex. Hence indexing collex by enrolment[survey] causes a 500

    :param enrolment_data: A list of enrolments.
    :type enrolment_data: list
    :param collection_exercises: A list of collection exercises.
    :type collection_exercises: list
    :return: list of enrolments corresponding to the known collection exercises
    """

    enrolments = []
    for enrolment in enrolment_data:
        if enrolment["survey_id"] in collection_exercises:
            enrolments.append(enrolment)
    return enrolments


def get_unique_survey_and_business_ids(enrolment_data):
    """Takes a list of enrolment data and returns 2 unique sets of business_id and party_id's

    :param enrolment_data: A list of enrolments
    :return: A pair of sets with deduplicated survey_id's and business_id's
    """

    surveys_ids = set()
    business_ids = set()
    for enrolment in enrolment_data:
        surveys_ids.add(enrolment["survey_id"])
        business_ids.add(enrolment["business_id"])
    return surveys_ids, business_ids


def caching_case_data(cache_data, business_ids, tag):
    # Creates a list of threads which will call functions to set the case in the cache_data.
    threads = []

    for business_id in business_ids:
        threads.append(
            ThreadWrapper(get_case, cache_data, business_id, app.config["CASE_URL"], app.config["BASIC_AUTH"], tag)
        )

    for thread in threads:
        thread.start()

    # We do a thread join to make sure that the threads have all terminated before it carries on
    for thread in threads:
        thread.join()


def get_survey_list_details_for_party(respondent: dict, tag: str, business_party_id: str, survey_id: str):
    """
    Gets a list of cases (and any useful metadata) for a respondent.  Depending on the tag the list of cases will be
    ones that require action (in the form of an EQ or SEFT submission); Or they will be cases that have been completed
    and are used to see what has been submitted in the past.

    This function uses caching to get data from Case, Party, Collection exercise, Survey and
    Collection Instrument services. Without this, respondents with a large number of cases can experience page timeouts
    as it'll take too long to load due to repeated calls for the same information from the services.

    There isn't a direct link between respondent and the cases they're involved in.  Instead we can work out what
    cases they're involved in via an implicit and indirect link between:
        - The combination of survey and business a respondent is enrolled for, and;
        - the cases and collection exercises the business is involved in

    The algorithm for determining this is roughly:
      - Get all survey enrolments for the respondent
      - For each enrolment:
          - Get the business details the enrolment is for
          - Get the live collection exercises for the survey the enrolment is for
          - Get the cases the business is part of, from the list of collection exercises. Note, this isn't every case
            against the business; depending on if you're looking at the to-do or history page, you'll get a different
            subset of them.
          - For each case in this list:
              - Create an entry in the returned list for each of these cases as the respondent is implicitly part
                of the case by being enrolled for the survey with that business.

    :param respondent: A dict containing respondent data
    :param tag: This is the page that is being called e.g. to-do, history
    :param business_party_id: This is the businesses uuid
    :param survey_id: This is the surveys uuid

    """
    enrolment_data = list(get_respondent_enrolments(respondent))

    # Gets the survey ids and business ids from the enrolment data that has been generated.
    # Converted to list to avoid multiple calls to party (and the list size is small).
    surveys_ids, business_ids = get_unique_survey_and_business_ids(enrolment_data)

    # This is a dictionary that will store all the data that is going to be cached instead of making multiple calls
    # inside the for loop for get_respondent_enrolments.
    cache_data = {"cases": dict()}
    redis_cache = RedisCache()

    # Populate the cache with all case data
    caching_case_data(cache_data, business_ids, tag)

    #  Populate the enrolments by creating a dictionary using the redis_cache
    collection_exercises = {
        survey_id: redis_cache.get_collection_exercises_by_survey(survey_id) for survey_id in surveys_ids
    }
    enrolments = get_respondent_enrolments_for_started_collex(enrolment_data, collection_exercises)

    for enrolment in enrolments:
        business_party = redis_cache.get_business_party(enrolment["business_id"])
        survey = redis_cache.get_survey(enrolment["survey_id"])

        live_collection_exercises = collection_exercises[enrolment["survey_id"]]

        collection_exercises_by_id = dict((ce["id"], ce) for ce in live_collection_exercises)
        cases_for_business = cache_data["cases"][business_party["id"]]

        # Gets all the cases for reporting unit, and by extension the user (because it's related to the business)
        enrolled_cases = [
            case
            for case in cases_for_business
            if case["caseGroup"]["collectionExerciseId"] in collection_exercises_by_id.keys()
        ]

        for case in enrolled_cases:
            collection_exercise = collection_exercises_by_id[case["caseGroup"]["collectionExerciseId"]]
            collection_instrument = redis_cache.get_collection_instrument(case["collectionInstrumentId"])
            collection_instrument_type = collection_instrument["type"]
            added_survey = True if business_party_id == business_party["id"] and survey_id == survey["id"] else None
            display_access_button = display_button(case["caseGroup"]["caseGroupStatus"], collection_instrument_type)

            yield {
                "case_id": case["id"],
                "status": case_controller.calculate_case_status(
                    case["caseGroup"]["caseGroupStatus"],
                    collection_instrument_type,
                ),
                "collection_instrument_type": collection_instrument_type,
                "survey_id": survey["id"],
                "survey_long_name": survey["longName"],
                "survey_short_name": survey["shortName"],
                "survey_ref": survey["surveyRef"],
                "business_party_id": business_party["id"],
                "business_name": business_party["name"],
                "trading_as": business_party["trading_as"],
                "business_ref": business_party["sampleUnitRef"],
                "period": collection_exercise["userDescription"],
                "period_ref": collection_exercise["exerciseRef"],
                "submit_by": collection_exercise["events"]["return_by"]["date"],
                "formatted_submit_by": collection_exercise["events"]["return_by"]["formatted_date"],
                "due_in": collection_exercise["events"]["return_by"]["due_time"],
                "collection_exercise_ref": collection_exercise["exerciseRef"],
                "collection_exercise_id": collection_exercise["id"],
                "added_survey": added_survey,
                "display_button": display_access_button,
            }


def get_case(cache_data, business_id, case_url, case_auth, tag):
    cache_data["cases"][business_id] = case_controller.get_cases_for_list_type_by_party_id(
        business_id, case_url, case_auth, tag
    )


def display_button(status, ci_type):
    return not (ci_type == "EQ" and status in CLOSED_STATE)


def is_respondent_enrolled(party_id: str, business_party_id: str, survey: dict) -> bool:
    respondent = get_respondent_party_by_id(party_id)
    enrolments = get_respondent_enrolments(respondent)
    for enrolment in enrolments:
        if enrolment["business_id"] == business_party_id and enrolment["survey_id"] == survey["id"]:
            return True
    return False


def notify_party_and_respondent_account_locked(respondent_id, email_address, status=None):
    bound_logger = logger.bind(respondent_id=respondent_id, email=obfuscate_email(email_address), status=status)
    bound_logger.info("Notifying respondent and party service that account is locked")
    url = f'{app.config["PARTY_URL"]}/party-api/v1/respondents/edit-account-status/{respondent_id}'

    data = {"respondent_id": respondent_id, "email_address": email_address, "status_change": status}

    response = requests.put(url, json=data, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        bound_logger.error("Failed to notify party")
        bound_logger.unbind("respondent_id", "email", "status")
        raise ApiError(logger, response)

    bound_logger.info("Successfully notified respondent and party service that account is locked")
    bound_logger.unbind("respondent_id", "email", "status")


def get_list_of_business_for_party(party_id: str) -> list:
    """
    Gets the details for the businesses associated with a respondent
    :param party_id: respondent party id
    :return: list of businesses
    """
    logger.info("Getting enrolment data for the party", party_id=party_id)
    respondent = get_respondent_party_by_id(party_id)
    enrolment_data = get_respondent_enrolments(respondent)
    business_ids = {enrolment["business_id"] for enrolment in enrolment_data}
    logger.info("Getting businesses against business ids", business_ids=business_ids, party_id=party_id)
    return get_business_by_id(business_ids)


def get_business_by_id(business_ids: list) -> list:
    """
    Gets the business details for all the business_id's that are provided (
    :param business_ids: This takes a single business id or a list of business ids
    :return: List of business
    """
    logger.info("Attempting to fetch businesses", business_ids=business_ids)
    params = {"id": business_ids}
    url = f'{app.config["PARTY_URL"]}/party-api/v1/businesses'
    response = requests.get(url, params=params, auth=app.config["BASIC_AUTH"])
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response)
    return response.json()


def get_surveys_listed_against_party_and_business_id(business_id: str, party_id: str) -> list:
    """
    returns list of surveys associated with a business id and respondent
    :param business_id: business id
    :param party_id: The respondent's party id
    :return: list of surveys
    """
    respondent = get_respondent_party_by_id(party_id)
    enrolment_data = get_respondent_enrolments(respondent)
    survey_ids = {enrolment["survey_id"] for enrolment in enrolment_data if enrolment["business_id"] == business_id}
    surveys = []
    for survey in survey_ids:
        response = survey_controller.get_survey(app.config["SURVEY_URL"], app.config["BASIC_AUTH"], survey)
        surveys.append(response)
    return surveys


def get_user_count_registered_against_business_and_survey(business_id: str, survey_id: str, is_transfer) -> int:
    """
    returns total number of users registered against a business and survey

    :param business_id: business id
    :param survey_id: The survey id
    :param is_transfer: True if the request is for transfer survey
    :return: total number of users
    """
    logger.info("Attempting to get user count", business_ids=business_id, survey_id=survey_id)
    url = f'{app.config["PARTY_URL"]}/party-api/v1/pending-survey-users-count'
    data = {"business_id": business_id, "survey_id": survey_id, "is_transfer": is_transfer}
    response = requests.get(url, params=data, auth=app.config["BASIC_AUTH"])
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise ApiError(logger, response)
    return response.json()


def register_pending_shares(payload):
    """
    register new entries to party for pending shares

    :param payload: pending shares entries dict
    :return: success if post completed
    :rtype: response object
    """
    logger.info("Attempting register pending shares")
    url = f'{app.config["PARTY_URL"]}/party-api/v1/pending-surveys'
    response = requests.post(url, json=json.loads(payload), auth=app.config["BASIC_AUTH"])
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 400:
            logger.info("share survey has already been shared, hence ignoring this request.")
        else:
            raise ApiError(logger, response)
    return response


def get_pending_surveys_batch_number(batch_no):
    """
    Gets batch number for the shared survey

    :param batch_no: Shared survey batch number
    :type batch_no: str
    :raises ApiError: Raised when party returns api error
    :return: list share surveys
    """
    logger.info("Attempting to retrieve share surveys by batch number", batch_no=batch_no)
    url = f"{app.config['PARTY_URL']}/party-api/v1/pending-surveys/{batch_no}"
    response = requests.get(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to retrieve share surveys by batch number", batch_no=batch_no)
        raise ApiError(logger, response)

    logger.info("Successfully retrieved share surveys by batch number", batch_no=batch_no)
    return response


def create_pending_survey_account(registration_data):
    """
    Gives call to party service to create a new account and register the account against the email address of share
    surveys/ transfer surveys
    :param registration_data: respondent details
    :type registration_data: dict
    :raises ApiError: Raised when party returns api error
    """
    logger.info("Attempting to create new account against share survey")

    url = f"{app.config['PARTY_URL']}/party-api/v1/pending-survey-respondent"
    registration_data["status"] = "ACTIVE"
    response = requests.post(url, auth=app.config["BASIC_AUTH"], json=registration_data)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 400:
            logger.info("Email has already been used")
        else:
            logger.error("Failed to create account")
        raise ApiError(logger, response)

    logger.info("Successfully created account")


def get_business_by_ru_ref(ru_ref: str):
    """
    Gives call to party service to retrieve a business using a ru_ref parameter
    :param ru_ref: the reporting unit reference
    :returns: a business
    :raises ApiError: Raised when party returns api error
    """
    logger.info("Attempting to retrieve business by ru_ref", ru_ref=ru_ref)

    url = f"{app.config['PARTY_URL']}/party-api/v1/businesses/ref/{ru_ref}"
    response = requests.get(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error("Failed to retrieve business by ru_ref", ru_ref=ru_ref)
        raise ApiError(logger, response)

    logger.info("Successfully retrieved business by ru_ref", ru_ref=ru_ref)

    return response.json()


def get_verification_token(party_id):
    """
    Gives call to party service to retrieve a verification token for the respondent
    :param party_id: the respondent's id
    :returns: verification token
    """
    logger.info("Attempting to retrieve respondent verification token", party_id=party_id)
    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/{party_id}/password-verification-token"
    response = requests.get(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.HTTPError:
        if response == 404:
            logger.error("Verification token not found")
            raise NotFound("Token not found")
        logger.error("Failed to retrieve verification token", party_id=party_id)
        raise ApiError(logger, response)

    logger.info("Successfully retrieved verification token")

    return response.json()


def post_verification_token(email, token):
    """
    Gives call to party service to add a verification token for the respondent and increase the password reset counter
    :param email: the respondent's email
    :param token: the verification token
    """
    logger.info(
        "Attempting to add respondent verification token and increase password reset counter",
        email=obfuscate_email(email),
    )

    party_id = get_respondent_by_email(email)["id"]
    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/{party_id}/password-verification-token"
    payload = {
        "token": token,
    }
    response = requests.post(url, auth=app.config["BASIC_AUTH"], json=payload)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        logger.error(
            "Failed to add respondent verification token or increase password reset counter",
            email=obfuscate_email(email),
        )
        raise ApiError(logger, response)

    logger.info(
        "Successfully added respondent verification token and password reset counter", email=obfuscate_email(email)
    )

    return response.json()


def delete_verification_token(token):
    """
    Gives call to party service to delete a verification token for the respondent
    :param token: the verification token
    """
    email = decode_email_token(token)
    logger.info("Attempting to delete respondent verification token", email=obfuscate_email(email))

    party_id = get_respondent_by_email(email)["id"]
    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/{party_id}/password-verification-token/{token}"
    response = requests.delete(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            logger.error("Verification token not found")
            raise NotFound("Token not found")
        logger.error("Failed to delete respondent verification token", email=obfuscate_email(email))
        raise ApiError(logger, response)

    logger.info("Successfully deleted respondent verification token", email=obfuscate_email(email))

    return response.json()


def get_password_reset_counter(party_id):
    """
    Gives call to the party service to retrieve the password reset counter for the respondent
    :param party_id: the respondent's id
    :returns: current number of password reset attempts
    """

    logger.info("Attempting to retrieve respondent password reset counter", party_id=party_id)
    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/{party_id}/password-reset-counter"
    response = requests.get(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            logger.error("Counter not found")
            raise NotFound("Counter not found")
        logger.error("Failed to retrieve password reset counter", party_id=party_id)
        raise ApiError(logger, response)

    logger.info("Successfully retrieved password reset counter")
    return response.json()


def reset_password_reset_counter(party_id):
    """
    Gives call to the party service to reset the password reset counter for the respondent
    :param party_id: the respondent's id
    """

    logger.info("Attempting to reset respondent password reset counter", party_id=party_id)
    url = f"{app.config['PARTY_URL']}/party-api/v1/respondents/{party_id}/password-reset-counter"
    response = requests.delete(url, auth=app.config["BASIC_AUTH"])

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            logger.error("Counter not found")
            raise NotFound("Counter not found")
        logger.error("Failed to reset password reset counter", party_id=party_id)
        raise ApiError(logger, response)

    logger.info("Successfully reset password reset counter")
    return response.json()
