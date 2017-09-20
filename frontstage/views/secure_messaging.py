import logging

from flask import Blueprint, json, redirect, render_template, request, session, url_for
from frontstage.common.authorisation import jwt_authorization
import requests
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import ExternalServiceError


logger = wrap_logger(logging.getLogger(__name__))

modify_data = {'action': '',
               'label': ''}

secure_message_bp = Blueprint('secure_message_bp', __name__, static_folder='static', template_folder='templates')


def get_party_ru_id(party_id):
    url = app.config['RAS_PARTY_GET_BY_RESPONDENT'].format(app.config['RAS_PARTY_SERVICE'], party_id)
    logger.debug('Retrieving ru_id', party_id=party_id)
    party_response = requests.get(url, auth=app.config['BASIC_AUTH'])
    if party_response.status_code == 404:
        logger.error('No respondent found in party service', party_id=party_id)
        return None
    elif party_response.status_code != 200:
        logger.error('Failed to retrieve ru_id')
        raise ExternalServiceError(party_response)
    party_response_json = party_response.json()
    associations = party_response_json.get('associations')
    if associations:
        ru_id = associations[0].get('partyId')
    else:
        logger.error('Respondent has no associations', party_id=party_id)
        ru_id = None
    return ru_id


def get_collection_case(party_id):
    url = app.config['RM_CASE_GET_BY_PARTY'].format(app.config['RM_CASE_SERVICE'], party_id)
    logger.debug('Retrieving collection case id', party_id=party_id)
    collection_response = requests.get(url, auth=app.config['BASIC_AUTH'])
    if collection_response.status_code == 204:
        logger.error('No case found', party_id=party_id)
        return None
    elif collection_response.status_code != 200:
        logger.error('Failed to retrieve collection case id', party_id=party_id)
        raise ExternalServiceError(collection_response)
    collection_response_json = collection_response.json()
    return collection_response_json[0].get('id')


def get_survey_id(party_id):
    url = app.config['RAS_PARTY_GET_BY_RESPONDENT'].format(app.config['RAS_PARTY_SERVICE'], party_id)
    logger.debug('Retrieving survey id', party_id=party_id)
    survey_response = requests.get(url, auth=app.config['BASIC_AUTH'])
    if survey_response is None:
        logger.error('No respondent found in party service', party_id=party_id)
        return None
    elif survey_response.status_code != 200:
        logger.error('Failed to retrieve survey id', party_id=party_id)
        raise ExternalServiceError(survey_response)
    survey_response_json = survey_response.json()
    associations = survey_response_json.get('associations')
    if associations:
        survey_name = associations[0].get('enrolments')[0].get('surveyId')
    else:
        logger.error('Respondent has no associations', party_id=party_id)
        survey_name = None
    return survey_name


@secure_message_bp.route('/create-message', methods=['GET', 'POST'])
@jwt_authorization(request)
def create_message(session):
    """Handles sending of new message"""
    if request.method == 'POST':
        party_id = session['party_id']
        loggerb = logger.bind(party_id=party_id)

        collection_case = get_collection_case(party_id)
        if collection_case is None:
            return redirect(url_for('error_bp.default_error_page'))
        ru_id = get_party_ru_id(party_id)
        if ru_id is None:
            return redirect(url_for('error_bp.default_error_page'))
        survey_name = get_survey_id(party_id)
        if survey_name is None:
            return redirect(url_for('error_bp.default_error_page'))

        data = {'msg_to': ['BRES'],
                'msg_from': session['party_id'],
                'subject': request.form['secure-message-subject'],
                'body': request.form['secure-message-body'],
                'thread_id': request.form['secure-message-thread-id'],
                'collection_case': collection_case,
                'ru_id': ru_id,
                'survey': survey_name}

        # Message already saved as draft
        if "msg_id" in request.form:
            data["msg_id"] = request.form['msg_id']
            loggerb = loggerb.bind(message_id=data["msg_id"])
            loggerb.debug('Message already exists as draft')

        if request.form['submit'] == 'Send':
            response = send_message(data, loggerb)
            if response.status_code == 400:
                logger.warning("Bad request to secure message service")
                errors = json.loads(response.content)
                return render_template('secure-messages/secure-messages-view.html',
                                       _theme='default',
                                       draft=data,
                                       errors=errors)
            message = json.loads(response.text)
            logger.debug('Secure Message sent successfully', message_id=message['msg_id'])
            return render_template('secure-messages/message-success-temp.html', _theme='default')

        if request.form['submit'] == 'Save draft':
            if "msg_id" in request.form:
                loggerb.info('Attempting to modify draft')
                response = modify_draft(data, loggerb)
                if response.status_code == 400:
                    logger.warning("Bad request to secure message service")
                    errors = json.loads(response.content)
                    return render_template('secure-messages/secure-messages-view.html',
                                           _theme='default',
                                           draft=data,
                                           errors=errors)
            else:
                loggerb.info("Attempting to save draft")
                response = save_draft(data, loggerb)
                if response.status_code == 400:
                    logger.warning("Bad request to secure message service")
                    errors = json.loads(response.content)
                    return render_template('secure-messages/secure-messages-view.html',
                                           _theme='default',
                                           draft=data,
                                           errors=errors)
            response_data = json.loads(response.text)
            loggerb.info('Saved draft successfully', message_id=response_data['msg_id'])
            return draft_get(response_data['msg_id'])

    return render_template('secure-messages/secure-messages-view.html', _theme='default', message={})


def get_message(message_id, logger):
    headers = {"Authorization": request.cookies['authorization']}
    url = app.config['MESSAGE_GET_URL'].format(message_id)
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logger.error('Failed to retrieve message')
        raise ExternalServiceError(response)
    logger.debug('Retrieved message successfully')
    return response


def get_thread_message(thread_id, logger):
    headers = {"Authorization": request.cookies['authorization']}
    url = app.config['THREAD_GET_API_URL'].format(thread_id)
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logger.error('Failed to retrieve thread', thread_id=thread_id)
        raise ExternalServiceError(response)
    thread = json.loads(response.text)
    for message in thread['messages']:
        if message.get('sent_date'):
            return message


def get_draft(draft_id, logger):
    headers = {"Authorization": request.cookies['authorization']}
    logger.debug('Retrieving draft')
    url = app.config['DRAFT_GET_API_URL'].format(draft_id)
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        logger.error('Failed to retrieve draft')
        raise ExternalServiceError(response)
    logger.info('Retrieved draft successfully')
    return response


def save_draft(data, logger):
    headers = {"Authorization": request.cookies['authorization']}
    logger.info("Attempting to save draft")
    url = app.config['DRAFT_SAVE_API_URL']
    response = requests.post(url, json=data, headers=headers)
    if response.status_code != 201 and response.status_code != 400:
        logger.error("Failed to save draft")
        raise ExternalServiceError(response)
    return response


def modify_draft(data, logger):
    headers = {"Authorization": request.cookies['authorization']}
    logger.info('Attempting to modify draft')
    url = app.config['DRAFT_PUT_API_URL'].format(request.form['msg_id'])
    response = requests.put(url, json=data, headers=headers)
    if response.status_code != 200 and response.status_code != 400:
        logger.error("Failed to modify draft")
        raise ExternalServiceError(response)
    return response


def send_message(data, logger):
    headers = {"Authorization": request.cookies['authorization']}
    logger.info("Attempting to send message")
    url = app.config['CREATE_MESSAGE_API_URL']
    response = requests.post(url, json=data, headers=headers)
    if response.status_code != 201 and response.status_code != 400:
        logger.error('Failed to create message')
        raise ExternalServiceError(response)
    return response


def remove_unread_label(message_id, logger):
    headers = {"Authorization": request.cookies['authorization']}
    logger.debug('Attempting to remove unread label')
    data = {"label": 'UNREAD', "action": 'remove'}
    url = app.config['MESSAGE_MODIFY_URL'].format(message_id)
    response = requests.put(url, json=data, headers=headers)
    if response.status_code != 200:
        logger.error("Failed to remove unread label")
        return False
    return True


@secure_message_bp.route('/draft/<draft_id>', methods=['GET'])
@jwt_authorization(request)
def draft_get(session, draft_id):
    """Get draft message"""
    party_id = session['party_id']
    loggerb = logger.bind(message_id=draft_id, party_id=party_id)
    response = get_draft(draft_id, logger)
    draft = json.loads(response.text)
    thread_id = draft.get('thread_id')
    if thread_id != draft['msg_id']:
        logger.debug('Attempting to retrieve thread', thread_id=thread_id)
        message = get_thread_message(thread_id, loggerb)
    else:
        message = None
    return render_template('secure-messages/secure-messages-view.html',
                           _theme='default',
                           draft=draft,
                           message=message,
                           label='DRAFT')


@secure_message_bp.route('/sent/<sent_id>', methods=['GET'])
@jwt_authorization(request)
def sent_get(session, sent_id):
    """Get sent message"""
    party_id = session['party_id']
    loggerb = logger.bind(message_id=sent_id, party_id=party_id)
    response = get_message(sent_id, logger)
    message = json.loads(response.text)
    loggerb.info('Retrieved message successfully')
    return render_template('secure-messages/secure-messages-view.html',
                           _theme='default',
                           message=message,
                           label='SENT')


@secure_message_bp.route('/message/<message_id>', methods=['GET'])
@jwt_authorization(request)
def message_get(session, message_id):
    """Get message"""
    party_id = session['party_id']
    loggerb = logger.bind(message_id=message_id, party_id=party_id)
    loggerb.debug('Retrieving message')
    response = get_message(message_id, loggerb)
    message = json.loads(response.text)
    remove_unread_label(message_id, loggerb)
    return render_template('secure-messages/secure-messages-view.html',
                           _theme='default',
                           message=message,
                           label='INBOX')


@secure_message_bp.route('/messages/', methods=['GET'])
@secure_message_bp.route('/messages/<label>', methods=['GET'])
@jwt_authorization(request)
def messages_get(session, label="INBOX"):
    """Gets users messages"""
    party_id = session['party_id']
    headers = {"Authorization": request.cookies['authorization']}
    loggerb = logger.bind(party_id=party_id)
    loggerb.info('Attempting to retrieve messages', label=label)

    url = app.config['MESSAGES_API_URL']
    if label is not None:
        url = url + "&label=" + label

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        logger.error('Error retrieving user messages', label=label)
        raise ExternalServiceError(resp)

    response_data = json.loads(resp.text)

    labels = app.config['LABELS_GET_API_URL']

    unread_label_data = requests.get(labels, headers=headers)
    if unread_label_data.status_code != 200:
        logger.error('Failed to retrieve unread label data')
        unread_msg_total = {'total': '0'}
    else:
        unread_msg_total = json.loads(unread_label_data.text)

    logger.info('Retrieved messages successfully')
    return render_template('secure-messages/secure-messages.html', _theme='default', messages=response_data['messages'],
                           links=response_data['_links'], label=label, total=unread_msg_total['total'])
