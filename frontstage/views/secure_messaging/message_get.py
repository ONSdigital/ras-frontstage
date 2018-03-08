import logging

from flask import json, render_template, request
from frontstage.common.authorisation import jwt_authorization
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.session import SessionHandler
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import SecureMessagingForm
from frontstage.views.secure_messaging import secure_message_bp


logger = wrap_logger(logging.getLogger(__name__))


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
                           ru_ref=message_json['message'].get('ru_id'),
                           survey=message_json['message'].get('survey'),
                           case_id=message_json['message'].get('case_id'),
                           draft=message_json['draft'],
                           form=form,
                           label=label)


def create_headers():
    encoded_jwt = SessionHandler().get_encoded_jwt(request.cookies['authorization'])
    headers = {"jwt": encoded_jwt}
    return headers


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
