import logging

from flask import Blueprint, json, render_template, request
from frontstage.common.authorisation import jwt_authorization
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.session import SessionHandler
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import SecureMessagingForm


logger = wrap_logger(logging.getLogger(__name__))

modify_data = {'action': '',
               'label': ''}

secure_message_bp = Blueprint('secure_message_bp', __name__, static_folder='static', template_folder='templates')


@secure_message_bp.route('/create-message', methods=['GET', 'POST'])
@jwt_authorization(request)
def create_message(session):
    party_id = session['party_id']
    form = SecureMessagingForm(request.form)
    if request.method == 'POST' and form.validate():
        is_draft = form.save_draft.data
        sent_message = send_message(party_id, is_draft)

        # If draft was saved retrieve the saved draft
        if is_draft:
            logger.info('Draft sent successfully', message_id=sent_message['msg_id'], party_id=party_id)
            return message_get('DRAFT', sent_message['msg_id'])

        return render_template('secure-messages/message-success-temp.html', _theme='default')

    else:
        message = get_message(form['thread_message_id'].data, 'INBOX', party_id) if form['thread_message_id'].data else {}
        return render_template('secure-messages/secure-messages-view.html', _theme='default', form=form, errors=form.errors, message=message.get('message', {}))


@secure_message_bp.route('/<label>/<message_id>', methods=['GET'])
@jwt_authorization(request)
def message_get(session, label, message_id):
    party_id = session['party_id']

    message_json = get_message(message_id, label, party_id)
    # Initialise SecureMessagingForm with values for the draft and hidden fields
    form = SecureMessagingForm(formdata=None,
                               thread_message_id=message_json['message'].get('msg_id'),
                               thread_id=message_json['message'].get('thread_id'),
                               msg_id=message_json['draft'].get('msg_id'),
                               hidden_subject=message_json['message'].get('subject'),
                               subject=message_json['draft'].get('subject'),
                               body=message_json['draft'].get('body'))
    return render_template('secure-messages/secure-messages-view.html',
                           _theme='default',
                           message=message_json['message'],
                           draft=message_json['draft'],
                           form=form,
                           label=label)


@secure_message_bp.route('/messages/', methods=['GET'])
@secure_message_bp.route('/messages/<label>', methods=['GET'])
@jwt_authorization(request)
def messages_get(session, label="INBOX"):
    messages_list = get_messages_list(label)
    messages = messages_list['messages']
    unread_msg_total = messages_list.get('unread_messages_total', 0)
    return render_template('secure-messages/secure-messages.html', _theme='default', messages=messages['messages'],
                           links=messages['_links'], label=label, total=unread_msg_total)


def get_messages_list(label):
    logger.debug('Attempting to retrieve messages', label=label)

    headers = create_headers()
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

    headers = create_headers()
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
    form = SecureMessagingForm(request.form)

    headers = create_headers()
    endpoint = app.config['SEND_MESSAGE_URL']
    subject = form['subject'].data if form['subject'].data else form['hidden_subject'].data
    message_json = {
        'msg_from': party_id,
        'subject': subject,
        'body': form['body'].data,
        'thread_id': form['thread_id'].data
    }

    # If message has previously been saved as a draft add through the message id
    if form["msg_id"].data:
        message_json["msg_id"] = form['msg_id'].data
    response = api_call('POST', endpoint, parameters={"is_draft": is_draft}, json=message_json, headers=headers)

    if response.status_code != 200:
        logger.debug('Failed to send message')
        raise ApiError(response)
    sent_message = json.loads(response.text)

    logger.info('Secure message sent successfully', message_id=sent_message['msg_id'], party_id=party_id)
    return sent_message


def create_headers():
    encoded_jwt = SessionHandler().get_encoded_jwt(request.cookies['authorization'])
    headers = {"jwt": encoded_jwt}
    return headers
