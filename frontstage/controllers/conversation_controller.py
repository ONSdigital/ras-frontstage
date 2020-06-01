import json
import logging
from json import JSONDecodeError

import requests
from flask import current_app, request
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError
from structlog import wrap_logger
from urllib3 import Retry

from frontstage.common.session import Session
from frontstage.exceptions.exceptions import ApiError, AuthorizationTokenMissing, NoMessagesError, IncorrectAccountAccessError


logger = wrap_logger(logging.getLogger(__name__))


def _get_session():
    session = requests.Session()
    retries = Retry(total=10, backoff_factor=0.1)
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session


def get_conversation(thread_id):
    logger.info('Retrieving conversation thread', thread_id=thread_id)

    headers = _create_get_conversation_headers()
    url = f"{current_app.config['SECURE_MESSAGE_URL']}/threads/{thread_id}"

    with _get_session() as session:
        response = session.get(url, headers=headers)
        try:
            response.raise_for_status()
        except HTTPError as exception:
            if exception.response.status_code == 403:
                raise IncorrectAccountAccessError(message='Access not granted for thread', thread_id=thread_id)
            else:
                logger.error('Thread retrieval failed', thread_id=thread_id)
                raise ApiError(response)

    logger.info('Successfully retrieved conversation thread', thread_id=thread_id)

    try:
        return response.json()
    except JSONDecodeError:
        logger.error('The thread response could not be decoded', thread_id=thread_id)
        raise ApiError(response)


def get_conversation_list(params):
    logger.info('Retrieving threads list')

    headers = _create_get_conversation_headers()
    url = f"{current_app.config['SECURE_MESSAGE_URL']}/threads"

    with _get_session() as session:
        response = session.get(url, headers=headers, params=params)
        try:
            response.raise_for_status()
        except HTTPError:
            logger.error('Threads retrieval failed')
            raise ApiError(response)

    logger.info('Successfully retrieved threads list')

    try:
        return response.json()['messages']
    except JSONDecodeError:
        logger.error('The threads response could not be decoded')
        raise ApiError(response)
    except KeyError:
        logger.error("Request was successful but didn't contain a 'messages' key")
        raise NoMessagesError


def send_message(message_json):
    party_id = json.loads(message_json).get('msg_from')
    logger.info('Sending message', party_id=party_id)

    url = f"{current_app.config['SECURE_MESSAGE_URL']}/messages"
    headers = _create_send_message_headers()

    with _get_session() as session:
        response = session.post(url, headers=headers, data=message_json)
        try:
            response.raise_for_status()
        except HTTPError:
            logger.error('Message sending failed due to API Error', party_id=party_id)
            raise ApiError(response)

    logger.info('Successfully sent message', party_id=party_id)
    return response.json()


def get_message_count(party_id, from_session=True):
    logger.info('Getting unread message count', party_id=party_id)

    session = Session.from_session_key(request.cookies['authorization'])
    if session.get_encoded_jwt() and from_session:
        logger.debug('Encoded JWT found, getting message count from session', party_id=party_id)
        if not session.message_count_expired():
            return session.get_unread_message_count()
        logger.debug('Unread Message count Redis timer has expired', party_id=party_id)

    logger.debug('Getting message count from secure-message api', party_id=party_id)
    params = {'new_respondent_conversations': True}
    headers = _create_get_conversation_headers()
    url = f"{current_app.config['SECURE_MESSAGE_URL']}/message/count"
    with _get_session() as requestSession:
        response = requestSession.get(url, headers=headers, params=params)
        try:
            response.raise_for_status()
            session.set_unread_message_total(response.body['total_count'])
            return response.body['total_count']
        except HTTPError as exception:
            if exception.response.status_code == 403:
                raise IncorrectAccountAccessError(message='User is unauthorized to perform this action', party_id=party_id)
            else:
                logger.error('An error has occured retrieving the new message count', party_id=party_id)
                return 0


def _create_get_conversation_headers():
    try:
        encoded_jwt = Session.from_session_key(request.cookies['authorization']).get_encoded_jwt()
    except KeyError:
        logger.error('Authorization token missing in cookie')
        raise AuthorizationTokenMissing
    return {'Authorization': encoded_jwt}


def _create_send_message_headers():
    try:
        encoded_jwt = Session.from_session_key(request.cookies['authorization']).get_encoded_jwt()
    except KeyError:
        logger.error('Authorization token missing in cookie')
        raise AuthorizationTokenMissing
    return {'Authorization': encoded_jwt, 'Content-Type': 'application/json', 'Accept': 'application/json'}


def remove_unread_label(message_id):
    logger.info('Removing message unread label', message_id=message_id)

    url = f"{current_app.config['SECURE_MESSAGE_URL']}/messages/modify/{message_id}"
    data = '{"label": "UNREAD", "action": "remove"}'
    headers = _create_send_message_headers()

    with _get_session() as session:
        response = session.put(url, headers=headers, data=data)
        try:
            response.raise_for_status()
        except HTTPError:
            logger.error('Failed to remove unread label', message_id=message_id, status=response.status_code)

    logger.info('Successfully removed unread label', message_id=message_id)
