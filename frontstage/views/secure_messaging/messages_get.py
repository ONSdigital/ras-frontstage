import logging

from flask import json, render_template, request
from frontstage.common.authorisation import jwt_authorization
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.exceptions.exceptions import ApiError
from frontstage.views.secure_messaging import secure_message_bp
from frontstage.views.secure_messaging.message_get import create_headers


logger = wrap_logger(logging.getLogger(__name__))


@secure_message_bp.route('/messages/', methods=['GET'])
@secure_message_bp.route('/messages/<label>', methods=['GET'])
@jwt_authorization(request)
def messages_get(session, label="INBOX"):
    messages_list = get_messages_list(label)
    messages = messages_list['messages']
    new_message = request.args.get('new_message', None)
    unread_msg_total = messages_list.get('unread_messages_total', 0)
    return render_template('secure-messages/secure-messages.html', _theme='default', messages=messages['messages'],
                           links=messages['_links'], label=label, total=unread_msg_total, new_message=new_message)


def get_messages_list(label):
    logger.debug('Attempting to retrieve messages list', label=label)

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
