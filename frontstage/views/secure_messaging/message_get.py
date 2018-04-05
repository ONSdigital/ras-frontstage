import logging

from flask import json, render_template, redirect, request, url_for
from frontstage.common.authorisation import jwt_authorization
from structlog import wrap_logger

from frontstage.common.message_helper import refine
from frontstage.controllers.conversation_controller import get_conversation, send_message, get_conversation_list
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
    logger.info("Successfully retrieved conversation", thread_id=thread_id)
    try:
        refined_conversation = [refine(message) for message in reversed(conversation)]
    except KeyError as e:
        logger.exception("Message is missing important data", thread_id=thread_id)
        raise

    form = SecureMessagingForm(request.form)
    form.subject.data = refined_conversation[0].get('subject')

    if form.validate_on_submit():
        logger.info("Sending message", thread_id=thread_id)
        send_message(_get_message_json(form, refined_conversation[0], party_id=session['party_id']))
        logger.info("Successfully sent message", thread_id=thread_id)
        return redirect(url_for('secure_message_bp.view_conversation_list', new_message=True))

    return render_template('secure-messages/conversation-view.html',
                           _theme='default',
                           form=form,
                           conversation=refined_conversation)


@secure_message_bp.route('/threads', methods=['GET'])
@jwt_authorization(request)
def view_conversation_list(session):
    logger.info("Getting conversation list")
    conversation = get_conversation_list()
    new_message = request.args.get('new_message', None)
    try:
        refined_conversation = [refine(message) for message in conversation]
    except KeyError as e:
        logger.exception("A key error occurred")
        raise ApiError(e)

    return render_template('secure-messages/conversation-list.html',
                           _theme='default',
                           messages=refined_conversation,
                           new_message=new_message)


def _get_message_json(form, message, party_id):
    return json.dumps({
        'msg_from': party_id,
        'msg_to': ["GROUP"],
        'subject': form.subject.data,
        'body': form.body.data,
        'thread_id': message['thread_id'],
        'collection_case': "",
        'survey': message['survey_id'],
        'ru_id': message['ru_ref']})
