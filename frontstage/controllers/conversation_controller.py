import json
import logging
from collections import namedtuple
from json import JSONDecodeError
from uuid import UUID

from flask import current_app, request
from requests import Session as request_session
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError, HTTPError, Timeout
from structlog import wrap_logger
from urllib3 import Retry

from frontstage.common.session import Session
from frontstage.exceptions.exceptions import (
    ApiError,
    AuthorizationTokenMissing,
    IncorrectAccountAccessError,
    NoMessagesError,
    ServiceUnavailableException,
)
from frontstage.models import SecureMessagingForm


class InvalidSecureMessagingForm(Exception):
    def __init__(self, errors: dict) -> None:
        super().__init__()
        self.errors = errors


logger = wrap_logger(logging.getLogger(__name__))

NOT_SURVEY_RELATED = "Not survey related"

Option = namedtuple("Option", ["value", "text"])

ORGANISATION_DISABLED_OPTION = {"value": "Choose an organisation", "text": "Choose an organisation", "disabled": True}
SURVEY_DISABLED_OPTION = {"value": "Choose a survey", "text": "Choose a survey", "disabled": True}
SUBJECT_DISABLED_OPTION = {"value": "Choose a subject", "text": "Choose a subject", "disabled": True}

SUBJECT_OPTIONS = [
    Option("Help with my survey", "Help with my survey"),
    Option("Technical difficulties", "Technical difficulties"),
    Option("Change business address", "Change business address"),
    Option("Feedback", "Feedback"),
    Option("Help transferring or sharing access to a survey", "Help transferring or sharing access to a survey"),
    Option("Something else", "Something else"),
]


def _get_session():
    session = request_session()
    retries = Retry(total=10, backoff_factor=0.1)
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def get_conversation(thread_id):
    logger.info("Retrieving conversation thread", thread_id=thread_id)

    headers = _create_get_conversation_headers()
    url = f"{current_app.config['SECURE_MESSAGE_URL']}/threads/{thread_id}"

    with _get_session() as session:
        response = session.get(url, headers=headers)
        try:
            response.raise_for_status()
        except HTTPError as exception:
            if exception.response.status_code == 403:
                raise IncorrectAccountAccessError(message="Access not granted for thread", thread_id=thread_id)
            else:
                logger.error("Thread retrieval failed", thread_id=thread_id)
                raise ApiError(logger, response)

    logger.info("Successfully retrieved conversation thread", thread_id=thread_id)

    try:
        return response.json()
    except JSONDecodeError:
        logger.error("The thread response could not be decoded", thread_id=thread_id)
        raise ApiError(logger, response)


def get_conversation_list(params):
    logger.info("Retrieving threads list")

    headers = _create_get_conversation_headers()
    url = f"{current_app.config['SECURE_MESSAGE_URL']}/threads"

    with _get_session() as session:
        response = session.get(url, headers=headers, params=params)
        try:
            response.raise_for_status()
        except HTTPError:
            logger.error("Threads retrieval failed")
            raise ApiError(logger, response)

    logger.info("Successfully retrieved threads list")

    try:
        return response.json()["messages"]
    except JSONDecodeError:
        logger.error("The threads response could not be decoded")
        raise ApiError(logger, response)
    except KeyError:
        logger.error("Request was successful but didn't contain a 'messages' key")
        raise NoMessagesError


def send_secure_message(form, msg_to=["GROUP"]) -> UUID:
    """
    Creates a message in the secure-message service
    """

    if not form.validate():
        raise InvalidSecureMessagingForm(form.errors)

    survey_id = None if form.survey_id.data == NOT_SURVEY_RELATED else form.survey_id.data
    business_id = form.business_id.data
    sm_version = current_app.config["SECURE_MESSAGE_VERSION"]
    session = _get_session()
    headers = _create_send_message_headers()

    if sm_version in ("v1", "both"):
        sm_v1_message_json = {
            "msg_from": form.party_id,
            "msg_to": msg_to,
            "subject": form.subject.data,
            "category": form.category,
            "body": form["body"].data,
            "thread_id": form.thread_id.data,
        }

        if survey_id:
            sm_v1_message_json["survey_id"] = survey_id
        if business_id:
            sm_v1_message_json["business_id"] = business_id

        url = f"{current_app.config['SECURE_MESSAGE_URL']}/messages"
        response = session.post(url, headers=headers, data=json.dumps(sm_v1_message_json))
        try:
            response.raise_for_status()
        except HTTPError:
            logger.error("Message sending failed due to API Error", party_id=form.party_id)
            raise ApiError(logger, response)

        sm_v1_msg_id = response.json()["msg_id"]

        logger.info(
            "Secure message sent successfully",
            message_id=sm_v1_msg_id,
            party_id=form.party_id,
            category=form.category,
            survey_id=survey_id,
            business_id=business_id,
        )

    if current_app.config["SECURE_MESSAGE_VERSION"] in ("v2", "both"):
        # This code was added due to an issue between the crossover of SM V1 and SM V2. The problem is outlined below:
        # SM V1 stores empty survey_ids as empty strings whereas SM V2 uses a 'None' value.
        # So this will break SM V2 which is implemented to except optional UUIDs.
        if survey_id == "":
            survey_id = None

        sm_v2_thread = {
            "subject": form.subject.data,
            "category": form.category,
            "ru_ref": business_id,
            "survey_id": survey_id,
            "respondent_id": form.party_id,
            "is_read_by_respondent": False,
            "is_read_by_internal": False,
        }
        sm_v2_thread_json = _post_to_secure_message_v2_threads(session, headers, sm_v2_thread)

        sm_v2_message = {
            "thread_id": sm_v2_thread_json["id"],
            "body": form["body"].data,
            "is_from_internal": False,
            "sent_by": form.party_id,
        }

        sm_v2_message_json = _post_to_secure_message_v2_messages(session, headers, sm_v2_message)

    return sm_v2_message_json["id"] if current_app.config["SECURE_MESSAGE_VERSION"] == "v2" else sm_v1_msg_id


def secure_message_enrolment_options(respondent_enrolments: dict, secure_message_form: SecureMessagingForm) -> dict:
    """returns a dict of secure message options based on a respondent_enrolments"""

    survey_options = _create_survey_options(respondent_enrolments)

    sm_enrolment_options = {
        "survey": _create_formatted_option_list(
            survey_options, secure_message_form.survey_id.data, SURVEY_DISABLED_OPTION
        ),
        "subject": _create_formatted_option_list(
            SUBJECT_OPTIONS, secure_message_form.subject.data, SUBJECT_DISABLED_OPTION
        ),
    }

    secure_message_form.business_id = respondent_enrolments["business_id"]

    return sm_enrolment_options


def secure_message_organisation_options(business_details: list) -> list:
    """returns a dict of business_options based on a business_details"""
    organisation_options = _create_organisation_options(business_details)
    return _create_formatted_option_list(organisation_options, "", ORGANISATION_DISABLED_OPTION)


def try_message_count_from_session(session):
    """Attempts to get the unread message count from the session,
    will fall back to the secure-message api if unsuccessful"""
    party_id = session.get_party_id()
    logger.debug("Getting message count from session", party_id=party_id)
    try:
        if not session.message_count_expired():
            return session.get_unread_message_count()
        logger.debug("Unread Message count timer has expired", party_id=party_id)
    except KeyError:
        logger.warn("Unread message count does not exist in the session", party_id=party_id)
    return get_message_count_from_api(session)


def get_message_count_from_api(session) -> int:
    """Gets the unread message count from the secure-message api.
    A successful get will update the session."""
    party_id = session.get_party_id()
    logger.info("Getting message count from secure-message api", party_id=party_id)
    params = {"unread_conversations": "true"}
    headers = _create_get_conversation_headers(session.get_encoded_jwt())
    url = f"{current_app.config['SECURE_MESSAGE_URL']}/messages/count"
    with _get_session() as requestSession:
        response = requestSession.get(url, headers=headers, params=params)
        try:
            response.raise_for_status()
            count = response.json()["total"]
            logger.debug("Got unread message count, updating session", party_id=party_id, count=count)
            if session.is_persisted():
                session.set_unread_message_total(count)
            return count
        except HTTPError as exception:
            if exception.response.status_code == 403:
                raise IncorrectAccountAccessError(
                    message="User is unauthorized to perform this action", thread_id=party_id
                )
            else:
                logger.exception("An error has occurred retrieving the new message count", party_id=party_id)
        except Exception:
            logger.exception(
                "An unknown error has occurred getting message count from secure-message api", party_id=party_id
            )
        return 0


def _create_survey_options(respondent_enrolments: dict) -> list:
    survey_options = [Option("Not survey related", "Not survey related")]
    for survey in respondent_enrolments["survey_details"]:
        survey_options.append(Option(survey["id"], survey["long_name"]))
    return survey_options


def _create_organisation_options(business_details: list) -> list:
    organisation_options = []
    for business in business_details:
        organisation_options.append(Option(business["business_id"], business["business_name"]))
    return organisation_options


def _create_formatted_option_list(options: list, selected: str, disabled_option: dict) -> list:
    formatted_option_list = [disabled_option]

    for option in sorted(options, key=lambda k: k.text):
        option_dict = {"value": option.value, "text": option.text}
        if selected == option.value:
            option_dict["selected"] = True
        formatted_option_list.append(option_dict)

    if not selected:
        formatted_option_list[0]["selected"] = True

    return formatted_option_list


def _create_get_conversation_headers(encoded_jwt=None) -> dict:
    try:
        if encoded_jwt is None:
            encoded_jwt = Session.from_session_key(request.cookies["authorization"]).get_encoded_jwt()
    except KeyError:
        logger.error("Authorization token missing in cookie")
        raise AuthorizationTokenMissing
    return {"Authorization": encoded_jwt}


def _create_send_message_headers() -> dict:
    try:
        encoded_jwt = Session.from_session_key(request.cookies["authorization"]).get_encoded_jwt()
    except KeyError:
        logger.error("Authorization token missing in cookie")
        raise AuthorizationTokenMissing
    return {"Authorization": encoded_jwt, "Content-Type": "application/json", "Accept": "application/json"}


def remove_unread_label(message_id: str):
    logger.info("Removing message unread label", message_id=message_id)

    url = f"{current_app.config['SECURE_MESSAGE_URL']}/messages/modify/{message_id}"
    data = '{"label": "UNREAD", "action": "remove"}'
    headers = _create_send_message_headers()

    with _get_session() as session:
        response = session.put(url, headers=headers, data=data)
        try:
            response.raise_for_status()
        except HTTPError:
            logger.error("Failed to remove unread label", message_id=message_id, status=response.status_code)

    logger.info("Successfully removed unread label", message_id=message_id)


def _post_to_secure_message_v2_threads(session: request_session, headers: dict, data: dict) -> dict:
    url = f"{current_app.config['SECURE_MESSAGE_V2_URL']}/threads"
    try:
        response = session.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
    except HTTPError:
        logger.error("Failed to create secure message v2 thread", status=response.status_code)
        raise ApiError(logger, response)
    except ConnectionError:
        raise ServiceUnavailableException("Secure message v2 returned a connection error", 503)
    except Timeout:
        raise ServiceUnavailableException("Secure message v2 has timed out", 504)
    return response.json()


def _post_to_secure_message_v2_messages(session: request_session, headers: dict, data: dict) -> dict:
    url = f"{current_app.config['SECURE_MESSAGE_V2_URL']}/messages"
    try:
        response = session.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
    except HTTPError:
        logger.error("Failed to create secure message v2 message", status=response.status_code)
        raise ApiError(logger, response)
    except ConnectionError:
        raise ServiceUnavailableException("Secure message v2 returned a connection error", 503)
    except Timeout:
        raise ServiceUnavailableException("Secure message v2 has timed out", 504)
    return response.json()
