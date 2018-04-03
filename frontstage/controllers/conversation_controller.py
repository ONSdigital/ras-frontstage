import requests

from json import JSONDecodeError
import logging

from flask import current_app, request
from frontstage.common.session import SessionHandler
from frontstage.exceptions.exceptions import ApiError
from requests.exceptions import HTTPError, RequestException
from structlog import wrap_logger

logger = wrap_logger(logging.getLogger(__name__))


def get_conversation(thread_id):
    logger.info("Retrieving conversation", thread_id=thread_id)

    headers = _create_get_conversation_headers()
    url = '{}v2/threads/{}'.format(current_app.config["RAS_SECURE_MESSAGE_SERVICE"], thread_id)

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except (HTTPError, RequestException):
        logger.exception("Thread retrieval failed", thread_id=thread_id)
        raise ApiError(response)
    logger.info("Thread retrieval successful", thread_id=thread_id)

    try:
        return response.json()
    except JSONDecodeError:
        logger.exception("the response could not be decoded", thread_id=thread_id)
        raise ApiError(response)


def send_message(message_json):
    logger.info("About to send message")
    url = '{}v2/messages'.format(current_app.config["RAS_SECURE_MESSAGE_SERVICE"])
    headers = _create_send_message_headers()
    try:
        response = requests.post(url, headers=headers, data=message_json)
        response.raise_for_status()
    except HTTPError as ex:
        logger.exception("Message sending failed due to API Error")
        raise ApiError(ex.response)
    logger.info("Message sent successfully")


def _create_get_conversation_headers():
    encoded_jwt = SessionHandler().get_encoded_jwt(request.cookies['authorization'])
    headers = {"Authorization": encoded_jwt}
    return headers


def _create_send_message_headers():
    encoded_jwt = SessionHandler().get_encoded_jwt(request.cookies['authorization'])
    headers = {"Authorization": encoded_jwt, 'Content-Type': 'application/json', 'Accept': 'application/json'}
    return headers
