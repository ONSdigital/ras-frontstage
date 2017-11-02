import logging

from flask import Blueprint, json, render_template, request
from frontstage.common.authorisation import jwt_authorization
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import ApiError
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
    unread_msg_total = messages_list.get('unread_messages_total', 0)
    return render_template('secure-messages/secure-messages.html', _theme='default', messages=messages['messages'],
                           links=messages['_links'], label=label, total=unread_msg_total)


def get_messages_list(label):
    logger.debug('Attempting to retrieve messages', label=label)

    # Form api request
    headers = {"Authorization": request.cookies['authorization']}
    endpoint = app.config['GET_MESSAGES_URL']
    parameters = {"label": label} if label else {}
    response = api_call('GET', endpoint, parameters=parameters, headers=headers)

    if response.status_code != 200:
        logger.error('Failed to retrieve messages list', label=label)
        raise ApiError(response)

    messages_list = json.loads(response.text)
    logger.debug('Retrieved messages list successfully', label=label)
    return messages_list


def get_message(message_id, label, party_id):
    logger.debug('Attempting to retrieve message', message_id=message_id, party_id=party_id)

    # Form api request
    headers = {"Authorization": request.cookies['authorization']}
    endpoint = app.config['GET_MESSAGE_URL']
    parameters = {"message_id": message_id, "label": label, "party_id": party_id}
    response = api_call('GET', endpoint, parameters=parameters, headers=headers)

    if response.status_code != 200:
        logger.error('Failed to retrieve message', message_id=message_id, party_id=party_id)
        raise ApiError(response)

    message = json.loads(response.text)
    logger.debug('Retrieved message successfully', message_id=message_id, party_id=party_id)
    return message


def send_message(party_id, is_draft):
    logger.debug('Attempting to send message', party_id=party_id)

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

    # If form errors are returned render them
    if response.status_code == 400:
        logger.debug('Form submitted with errors', party_id=party_id)
        error_message = json.loads(response.text).get('error', {}).get('data')

        return render_template('secure-messages/secure-messages-view.html',
                               _theme='default',
                               message=error_message.get('thread_message'),
                               draft=message_json,
                               errors=error_message.get('form_errors'))

    if response.status_code != 200:
        logger.debug('Failed to send message')
        raise ApiError(response)

    sent_message = json.loads(response.text)
    # If draft was saved render the saved draft
    if is_draft:
        logger.info('Draft sent successfully', message_id=sent_message['msg_id'], party_id=party_id)
        return message_get('DRAFT', sent_message['msg_id'])

    logger.info('Secure message sent successfully', message_id=sent_message['msg_id'], party_id=party_id)
    return render_template('secure-messages/message-success-temp.html', _theme='default')
