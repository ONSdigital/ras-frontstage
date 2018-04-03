import logging

from flask import json, render_template, request
from frontstage.common.authorisation import jwt_authorization
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.message_helper import refine
from frontstage.common.session import SessionHandler
from frontstage.controllers.conversation_controller import get_conversation, send_message
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import SecureMessagingForm
from frontstage.views.secure_messaging import secure_message_bp


logger = wrap_logger(logging.getLogger(__name__))


@secure_message_bp.route('/thread/<thread_id>', methods=['GET', 'POST'])
@jwt_authorization(request)
def view_conversation(session, thread_id):
    logger.info("Getting conversation", thread_id=thread_id)
    # TODO, do we really want to do a GET every time, even if we're POSTing? Rops does it this
    # way so we can get it working, then get it right.
    conversation = get_conversation(thread_id)['messages']
    try:
        refined_conversation = [refine(message) for message in reversed(conversation)]
    except KeyError as e:
        logger.exception("A key error occurred", thread_id=thread_id)
        raise ApiError(e)

    form = SecureMessagingForm(request.form)
    form.subject.data = conversation[0].get('subject')
    # TODO error handling?  I don't think we can get to this point if the thread doesnt exist
    # so we can probably get away with it.
    survey = conversation[0].get('survey_id')

    logger.info(conversation[0])

    if form.validate_on_submit():
        logger.info("Sending message", thread_id=thread_id)
        # TODO fix method signature.. this should be cleaner
        send_message(_get_message_json(form, conversation[0], session))
        logger.info("Successfully sent message", thread_id=thread_id)

    return render_template('secure-messages/conversation-view.html',
                           _theme='default',
                           form=form,
                           conversation=refined_conversation)


def _get_message_json(form, message, session):
    return json.dumps({
        'msg_from': session['party_id'],
        'msg_to': [form.hidden_to_uuid.data],
        'subject': form.subject.data,
        'body': form.body.data,
        'thread_id': message.get('thread_id'),
        'collection_case': "",
        'survey': message.get('survey'),
        'ru_id': form.hidden_to_ru_id.data})


@secure_message_bp.route('/<label>/<message_id>', methods=['GET'])
@jwt_authorization(request)
def message_get(session, label, message_id):
    party_id = session['party_id']

    message_json = get_message(message_id, label, party_id)
    # Initialise SecureMessagingForm with values for the draft and hidden fields
    draft = message_json['draft']
    message = message_json['message']
    form = SecureMessagingForm(formdata=None,
                               thread_message_id=message.get('msg_id'),
                               thread_id=message.get('thread_id'),
                               msg_id=draft.get('msg_id'),
                               hidden_subject=message.get('subject'),
                               subject=draft.get('subject'),
                               body=draft.get('body'))
    # TODO this whole function needs looking at. When getting a draft it should use the draft end point not message
    if label == "DRAFT":
        ru_ref = draft.get('ru_id')
        survey = draft.get('survey')
        case_id = draft.get('case_id')
    else:
        ru_ref = message.get('ru_id')
        survey = message.get('survey')
        case_id = message.get('case_id')

    return render_template('secure-messages/secure-messages-view.html',
                           _theme='default',
                           message=message,
                           ru_ref=ru_ref,
                           survey=survey,
                           case_id=case_id,
                           draft=draft,
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
