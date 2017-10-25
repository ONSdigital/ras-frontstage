import logging

from flask import Blueprint, json, render_template, request
from frontstage.common.authorisation import jwt_authorization
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import ApiError, ExternalServiceError
from frontstage.common.api_call import api_call


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
        is_draft = True if request.form['submit'] == 'Save draft' else False
        return send_message(party_id, is_draft)

    elif request.method == 'GET':
        return render_template('secure-messages/secure-messages-view.html', _theme='default', message={})


@secure_message_bp.route('/<label>/<message_id>', methods=['GET'])
@jwt_authorization(request)
def message_get(session, label, message_id):
    """Get message"""
    party_id = session['party_id']
    message_json = get_message(message_id, label, party_id)
    return render_template('secure-messages/secure-messages-view.html',
                           _theme='default',
                           message=message_json['message'],
                           draft=message_json['draft'],
                           label=label)


@secure_message_bp.route('/messages/', methods=['GET'])
@secure_message_bp.route('/messages/<label>', methods=['GET'])
@jwt_authorization(request)
def messages_get(session, label="INBOX"):
    """Gets users messages"""
    messages_list = get_messages_list(label)
    messages = messages_list['messages']
    unread_msg_total = messages_list.get('unread_messages_total', {}).get('total')
    return render_template('secure-messages/secure-messages.html', _theme='default', messages=messages['messages'],
                           links=messages['_links'], label=label, total=unread_msg_total)


def get_messages_list(label):
    logger.debug('Attempting to retrieve messages')

    # Form api request
    headers = {"Authorization": request.cookies['authorization']}
    endpoint = app.config['GET_MESSAGES_URL']
    parameters = {"label": label} if label else {}
    response = api_call('GET', endpoint, parameters=parameters, headers=headers)

    # Check for failure calling Frontstage API
    if response.status_code != 200:
        logger.error('Error connecting to frontstage api')
        raise ApiError('FA000')

    messages_list = json.loads(response.text)

    # Handle Api Error codes
    error_code = messages_list.get('error', {}).get('code')
    if error_code == 'FA001':
        logger.error('Failed to retrieve messages list')
        raise ApiError('FA001')
    elif error_code == 'FA002':
        logger.error('Could not retrieve unread message total')

    logger.debug('Retrieved messages list successfully')
    return messages_list


def get_message(message_id, label, party_id):
    logger.debug('Attempting to retrieve message')

    # Form api request
    headers = {"Authorization": request.cookies['authorization']}
    endpoint = app.config['GET_MESSAGE_URL']
    parameters = {"message_id": message_id, "label": label, "party_id": party_id}
    response = api_call('GET', endpoint, parameters=parameters, headers=headers)

    # Check for failure calling Frontstage API
    if response.status_code != 200:
        logger.error('Failed to retrieve message')
        raise ExternalServiceError(response)

    message = json.loads(response.text)

    # Handle Api Error codes
    error_code = message.get('error', {}).get('code')
    if error_code and error_code != 'FA005':
        logger.error('Failed to retrieve message')
        raise ApiError(error_code)

    logger.debug('Retrieved message successfully')
    return message


def send_message(party_id, is_draft):
    logger.debug('Attempting to retrieve message')

    # Form api request
    headers = {"Authorization": request.cookies['authorization']}
    endpoint = app.config['SEND_MESSAGE_URL']
    message_json = {
        'msg_from': party_id,
        'subject': request.form['secure-message-subject'],
        'body': request.form['secure-message-body'],
        'thread_id': request.form['secure-message-thread-id']
    }
    # If message has previously been saved as a draft add through the message id
    if "msg_id" in request.form:
        message_json["msg_id"] = request.form['msg_id']
    response = api_call('POST', endpoint, parameters={"is_draft": is_draft}, json=message_json, headers=headers)

    # Check for failure when calling Frontstage API
    if response.status_code != 200:
        logger.debug('Failed to send message')
        raise ExternalServiceError(response)

    sent_message = json.loads(response.text)

    # Handle Frontstage API Error codes
    if sent_message.get('error', {}).get('code') == 'FA006':
        logger.debug('Form submitted with errors')
        message = sent_message.get('error', {}).get('data', {}).get('thread_message')
        errors = sent_message['error']['data']['form_errors']
        return render_template('secure-messages/secure-messages-view.html',
                               _theme='default',
                               message=message,
                               draft=message_json,
                               errors=errors)
    elif sent_message.get('error'):
        raise ApiError(error_code=sent_message['error']['code'])

    # If draft was saved render the saved draft
    if is_draft:
        logger.info('Draft sent successfully', message_id=sent_message['msg_id'])
        return message_get('DRAFT', sent_message['msg_id'])

    logger.info('Secure message sent successfully', message_id=sent_message['msg_id'])
    return render_template('secure-messages/message-success-temp.html', _theme='default')
