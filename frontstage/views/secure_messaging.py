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


@secure_message_bp.route('/create-message', methods=['GET', 'POST'])
@jwt_authorization(request)
def create_message(session):
    """Handles sending of new message"""
    if request.method == 'POST':
        party_id = session['party_id']
        loggerb = logger.bind(party_id=party_id)

        # Get user details using party_id
        collection_case = get_collection_case(party_id)
        if collection_case is None:
            return redirect(url_for('error_bp.default_error_page'))
        ru_id = get_party_ru_id(party_id)
        if ru_id is None:
            return redirect(url_for('error_bp.default_error_page'))
        survey_name = get_survey_id(party_id)
        if survey_name is None:
            return redirect(url_for('error_bp.default_error_page'))

        # Create message object to send to secure-message service
        data = {'msg_to': ['BRES'],
                'msg_from': session['party_id'],
                'subject': request.form['secure-message-subject'],
                'body': request.form['secure-message-body'],
                'thread_id': request.form['secure-message-thread-id'],
                'collection_case': collection_case,
                'ru_id': ru_id,
                'survey': survey_name}

        # Set msg_id if message already saved as draft
        if "msg_id" in request.form:
            data["msg_id"] = request.form['msg_id']
            loggerb = loggerb.bind(message_id=data["msg_id"])

        if request.form['submit'] == 'Send':
            return send_message(data, loggerb)

        elif request.form['submit'] == 'Save draft':
            return save_draft(data, loggerb)

    return render_template('secure-messages/secure-messages-view.html', _theme='default', message={})


@secure_message_bp.route('/<label>/<message_id>', methods=['GET'])
@jwt_authorization(request)
def message_get(session, label, message_id):
    """Get message"""
    party_id = session['party_id']
    loggerb = logger.bind(message_id=message_id, party_id=party_id, label=label)
    message = get_message(message_id, label, loggerb)

    # If message is a draft try and get the last message from its thread
    if label == 'DRAFT':
        draft = message
        thread_id = draft.get('thread_id')
        if thread_id != draft['msg_id']:
            message = get_thread_message(thread_id, loggerb, party_id)
        else:
            message = None
    else:
        draft = {}

    if label == 'UNREAD':
        remove_unread_label(message_id, loggerb)

    return render_template('secure-messages/secure-messages-view.html',
                           _theme='default',
                           message=message,
                           draft=draft,
                           label=label)


@secure_message_bp.route('/messages/', methods=['GET'])
@secure_message_bp.route('/messages/<label>', methods=['GET'])
@jwt_authorization(request)
def messages_get(session, label="INBOX"):
    """Gets users messages"""
    party_id = session['party_id']
    loggerb = logger.bind(party_id=party_id, label=label)
    messages = get_messages(label, loggerb)
    unread_msg_total = get_unread_message_total(loggerb)
    return render_template('secure-messages/secure-messages.html', _theme='default', messages=messages['messages'],
                           links=messages['_links'], label=label, total=unread_msg_total['total'])


def get_party_ru_id(party_id):
    url = app.config['RAS_PARTY_GET_BY_RESPONDENT'].format(app.config['RAS_PARTY_SERVICE'], party_id)
    logger.debug('Retrieving ru_id', party_id=party_id)
    party_response = requests.get(url, auth=app.config['BASIC_AUTH'])
    if party_response.status_code == 404:
        logger.warning('No respondent found in party service', party_id=party_id)
        return None
    elif party_response.status_code != 200:
        logger.error('Failed to retrieve ru_id')
        raise ExternalServiceError(party_response)
    party_response_json = party_response.json()
    associations = party_response_json.get('associations')
    if associations:
        ru_id = associations[0].get('partyId')
        logger.debug('Successfully received ru_id', ru_id=ru_id)
    else:
        logger.error('Respondent has no associations', party_id=party_id)
        ru_id = None
    return ru_id


def get_collection_case(party_id):
    url = app.config['RM_CASE_GET_BY_PARTY'].format(app.config['RM_CASE_SERVICE'], party_id, "")
    logger.debug('Retrieving collection case id')
    collection_response = requests.get(url, auth=app.config['BASIC_AUTH'])
    if collection_response.status_code == 204:
        logger.warning('No case found')
        return None
    elif collection_response.status_code != 200:
        logger.error('Failed to retrieve collection case id')
        raise ExternalServiceError(collection_response)
    collection_response_json = collection_response.json()
    case_id = collection_response_json[0].get('id')
    logger.debug('Successfully received collection case', case_id=case_id)
    return case_id


def get_survey_id(party_id):
    url = app.config['RAS_PARTY_GET_BY_RESPONDENT'].format(app.config['RAS_PARTY_SERVICE'], party_id)
    logger.debug('Retrieving survey id', party_id=party_id)
    survey_response = requests.get(url, auth=app.config['BASIC_AUTH'])
    if survey_response == 404:
        logger.warning('No respondent found in party service', party_id=party_id)
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
    logger.debug('Successfully received survey name', survey_id=survey_name, party_id=party_id)
    return survey_name


def get_messages(label, logger):
    headers = {"Authorization": request.cookies['authorization']}
    logger.debug('Attempting to retrieve messages')
    url = app.config['MESSAGES_API_URL']
    if label is not None:
        url = url + "&label=" + label
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        logger.error('Error retrieving user messages')
        raise ExternalServiceError(response)
    else:
        return json.loads(response.text)


def get_unread_message_total(logger):
    headers = {"Authorization": request.cookies['authorization']}
    logger.debug('Attempting to get the unread message total')
    url = app.config['LABELS_GET_API_URL']
    unread_label_data = requests.get(url, headers=headers)

    if unread_label_data.status_code != 200:
        logger.error('Failed to retrieve unread label data')
        return {'total': '0'}
    else:
        return json.loads(unread_label_data.text)


def get_message(message_id, label, logger):
    headers = {"Authorization": request.cookies['authorization']}
    logger.debug('Attempting to retrieve message')
    if label == 'DRAFT':
        url = app.config['DRAFT_GET_API_URL'].format(message_id)
    else:
        url = app.config['MESSAGE_GET_URL'].format(message_id)
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        logger.error('Failed to retrieve message')
        raise ExternalServiceError(response)

    message = json.loads(response.text)
    logger.debug('Retrieved message successfully')
    return message


def get_thread_message(thread_id, logger, party_id):
    headers = {"Authorization": request.cookies['authorization']}
    logger.debug('Attempting to retrieve message from thread', thread_id=thread_id)
    url = app.config['THREAD_GET_API_URL'].format(thread_id)
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        logger.error('Failed to retrieve thread', thread_id=thread_id)
        raise ExternalServiceError(response)

    # Search through the messages in the thread and set message to the last message the user received
    thread = json.loads(response.text)
    for thread_message in thread['messages']:
        if thread_message['@msg_from']['id'] != party_id:
            message = thread_message
            break
    else:
        message = None
        logger.error('No message found in thread not belonging to the user')

    logger.debug('Retrieved message from thread successfully', thread_id=thread_id)
    return message


def process_form_errors(response, data, logger):
    logger.warning("Bad request to secure message service")
    errors = json.loads(response.content)

    if data.get('thread_id'):
        message = get_thread_message(data['thread_id'], logger, data['msg_from'])
    else:
        message = {}

    return render_template('secure-messages/secure-messages-view.html',
                           _theme='default',
                           message=message,
                           draft=data,
                           errors=errors)


def save_draft(data, logger):
    headers = {"Authorization": request.cookies['authorization']}
    logger.debug("Attempting to save draft")
    if data.get('msg_id'):
        url = app.config['DRAFT_PUT_API_URL'].format(data['msg_id'])
        response = requests.put(url, json=data, headers=headers)
    else:
        url = app.config['DRAFT_SAVE_API_URL']
        response = requests.post(url, json=data, headers=headers)

    if response.status_code == 400:
        logger.debug('Form submitted with errors')
        return process_form_errors(response, data, logger)
    elif response.status_code != 200 and response.status_code != 201:
        logger.error("Failed to save draft")
        raise ExternalServiceError(response)

    response_data = json.loads(response.text)
    logger.info('Saved draft successfully', message_id=response_data['msg_id'])
    return message_get(label='DRAFT', message_id=response_data['msg_id'])


def send_message(data, logger):
    headers = {"Authorization": request.cookies['authorization']}
    logger.debug("Attempting to send message")
    url = app.config['CREATE_MESSAGE_API_URL']
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 400:
        logger.debug('Form submitted with errors')
        return process_form_errors(response, data, logger)
    elif response.status_code != 201 and response.status_code != 400:
        logger.error('Failed to create message')
        raise ExternalServiceError(response)

    message = json.loads(response.text)
    logger.info('Secure Message sent successfully', message_id=message['msg_id'])
    return render_template('secure-messages/message-success-temp.html', _theme='default')


def remove_unread_label(message_id, logger):
    headers = {"Authorization": request.cookies['authorization']}
    logger.debug('Attempting to remove unread label')
    data = {"label": 'UNREAD', "action": 'remove'}
    url = app.config['MESSAGE_MODIFY_URL'].format(message_id)
    response = requests.put(url, json=data, headers=headers)

    if response.status_code != 200:
        logger.error("Failed to remove unread label")
        return False
    logger.debug("Removed unread label")
    return True
