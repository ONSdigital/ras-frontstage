import json
import logging
from json import JSONDecodeError

import requests
from flask import current_app, request
from requests.adapters import HTTPAdapter
from structlog import wrap_logger
from urllib3 import Retry

from frontstage.exceptions.exceptions import ApiError, AuthorizationTokenMissing, NoMessagesError
from requests.exceptions import HTTPError


logger = wrap_logger(logging.getLogger(__name__))


def _get_session():
    session = requests.Session()
    retries = Retry(total=10, backoff_factor=0.1)
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session


def get_conversation(thread_id):
    logger.debug('Attempting to retrieve thread', thread_id=thread_id)

    headers = _create_get_conversation_headers()
    url = f"{current_app.config['SECURE_MESSAGE_URL']}/v2/threads/{thread_id}"

    with _get_session() as session:
        response = session.get(url, headers=headers)
        try:
            response.raise_for_status()
        except HTTPError:
            raise ApiError(logger, response,
                           log_level='exception',
                           message='Thread retrieval failed',
                           thread_id=thread_id)

    logger.debug('Thread retrieval successful', thread_id=thread_id)

    try:
        return response.json()
    except JSONDecodeError:
        raise ApiError(logger, response,
                       log_level='exception',
                       message='The thread response could not be decoded',
                       thread_id=thread_id)


def get_conversation_list():
    logger.debug('Attempting to retrieve threads list')

    headers = _create_get_conversation_headers()
    url = f"{current_app.config['SECURE_MESSAGE_URL']}/threads"

    with _get_session() as session:
        response = session.get(url, headers=headers)
        try:
            response.raise_for_status()
        except HTTPError:
            raise ApiError(logger, response,
                           log_level='exception',
                           message='Threads retrieval failed')

    logger.debug('Threads retrieval successful')

    try:
        return response.json()['messages']
    except JSONDecodeError:
        raise ApiError(logger, response,
                       log_level='exception',
                       message='The threads response could not be decoded')
    except KeyError:
        logger.exception("Response was successful but didn't contain a 'messages' key")
        raise NoMessagesError


def send_message(message_json):
    party_id = json.loads(message_json).get('msg_from')
    logger.debug('Attempting to send message', party_id=party_id)

    url = f"{current_app.config['SECURE_MESSAGE_URL']}/v2/messages"
    headers = _create_send_message_headers()

    with _get_session() as session:
        response = session.post(url, headers=headers, data=message_json)
        try:
            response.raise_for_status()
        except HTTPError:
            raise ApiError(logger, response,
                           log_level='exception',
                           message='Message sending failed due to API Error',
                           party_id=party_id)

    logger.debug('Successfully sent message', party_id=party_id)
    return response.json()


def _create_get_conversation_headers():
    try:
        encoded_jwt = SessionHandler().get_encoded_jwt(request.cookies['authorization'])
    except KeyError:
        logger.exception('Authorization token missing in cookie')
        raise AuthorizationTokenMissing
    return {'Authorization': encoded_jwt}


def _create_send_message_headers():
    try:
        encoded_jwt = SessionHandler().get_encoded_jwt(request.cookies['authorization'])
    except KeyError:
        logger.exception('Authorization token missing in cookie')
        raise AuthorizationTokenMissing
    return {'Authorization': encoded_jwt, 'Content-Type': 'application/json', 'Accept': 'application/json'}


def remove_unread_label(message_id):
    logger.debug('Attempting to remove message unread label', message_id=message_id)

    url = f"{current_app.config['SECURE_MESSAGE_URL']}/v2/messages/modify/{message_id}"
    data = '{"label": "UNREAD", "action": "remove"}'
    headers = _create_send_message_headers()

    with _get_session() as session:
        response = session.put(url, headers=headers, data=data)
        try:
            response.raise_for_status()
        except HTTPError:
            logger.exception('Failed to remove unread label', message_id=message_id, status=response.status_code)

    logger.debug('Successfully removed unread label', message_id=message_id)
