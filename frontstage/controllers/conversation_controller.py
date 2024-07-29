import json
import logging
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


def send_message(
    form,
    party_id: UUID,
    subject: str,
    category: str,
    msg_to=["GROUP"],
    survey_id: UUID = None,
    business_id: UUID = None,
    ce_id: UUID = None,
) -> UUID:
    """
    Creates a message in the secure-message service
    """

    secure_message_form = SecureMessagingForm(form)
    if not secure_message_form.validate():
        raise InvalidSecureMessagingForm(secure_message_form.errors)

    body = secure_message_form["body"].data
    thread_id = secure_message_form["thread_id"].data
    sm_version = current_app.config["SECURE_MESSAGE_VERSION"]
    session = _get_session()
    headers = _create_send_message_headers()

    if sm_version in ("v1", "both"):
        sm_v1_message_json = {
            "msg_from": party_id,
            "msg_to": msg_to,
            "subject": subject,
            "category": category,
            "body": body,
            "thread_id": thread_id,
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
            logger.error("Message sending failed due to API Error", party_id=party_id, exc_info=True)
            raise ApiError(logger, response)

        sm_v1_msg_id = response.json()["msg_id"]

        logger.info(
            "Secure message sent successfully",
            message_id=sm_v1_msg_id,
            party_id=party_id,
            category=category,
            survey_id=survey_id,
            business_id=business_id,
            ce_id=ce_id,
        )

    if current_app.config["SECURE_MESSAGE_VERSION"] in ("v2", "both"):

        if not thread_id:
            sm_v2_thread = {
                "subject": subject,
                "category": category,
                "ru_ref": business_id,
                "survey_id": survey_id,
                "respondent_id": party_id,
                "is_read_by_respondent": False,
                "is_read_by_internal": False,
            }
            sm_v2_thread_json = _post_to_secure_message_v2(session, headers, "threads", sm_v2_thread)
            thread_id = sm_v2_thread_json["id"]

        sm_v2_message = {
            "thread_id": thread_id,
            "body": body,
            "is_from_internal": False,
            "sent_by": party_id,
        }

        sm_v2_message_json = _post_to_secure_message_v2(session, headers, "messages", sm_v2_message)

    return sm_v2_message_json["id"] if current_app.config["SECURE_MESSAGE_VERSION"] == "v2" else sm_v1_msg_id


def _post_to_secure_message_v2(session: request_session, headers: dict, endpoint: str, data: dict) -> dict:
    url = f"{current_app.config['SECURE_MESSAGE_V2_URL']}/{endpoint}"
    try:
        response = session.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
    except HTTPError:
        raise ApiError(logger, response)
    except ConnectionError:
        raise ServiceUnavailableException("Secure message v2 returned a connection error", 503)
    except Timeout:
        raise ServiceUnavailableException("Secure message v2 has timed out", 504)
    return response.json()


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
