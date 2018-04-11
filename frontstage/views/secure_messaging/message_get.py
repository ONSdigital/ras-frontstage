import logging

from flask import json, flash, Markup, render_template, redirect, request, url_for

from frontstage.common.authorisation import jwt_authorization
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.message_helper import refine
from frontstage.common.session import SessionHandler
from frontstage.controllers.conversation_controller import get_conversation, get_conversation_list,\
    remove_unread_label, send_message
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import SecureMessagingForm
from frontstage.views.secure_messaging import secure_message_bp


logger = wrap_logger(logging.getLogger(__name__))


@secure_message_bp.route('/thread/<thread_id>', methods=['GET', 'POST'])
@jwt_authorization(request)
def view_conversation(session, thread_id):
    party_id = session.get('party_id')
    logger.info("Getting conversation", thread_id=thread_id, party_id=party_id)
    # TODO, do we really want to do a GET every time, even if we're POSTing? Rops does it this
    # way so we can get it working, then get it right.
    conversation = get_conversation(thread_id)['messages']
    logger.info("Successfully retrieved conversation", thread_id=thread_id, party_id=party_id)
    try:
        refined_conversation = [refine(message) for message in reversed(conversation)]
    except KeyError as e:
        logger.exception("Message is missing important data", thread_id=thread_id, party_id=party_id)
        raise ApiError(e)

    if refined_conversation[-1]['unread']:
        remove_unread_label(refined_conversation[-1]['message_id'])

    form = SecureMessagingForm(request.form)
    form.subject.data = refined_conversation[0].get('subject')

    if form.validate_on_submit():
        logger.info("Sending message", thread_id=thread_id, party_id=party_id)
        send_message(_get_message_json(form, refined_conversation[0], party_id=session['party_id']))
        logger.info("Successfully sent message", thread_id=thread_id, party_id=party_id)
        thread_url = url_for("secure_message_bp.view_conversation", thread_id=thread_id) + "#latest-message"
        flash(Markup('Message sent. <a href={}>View Message</a>'.format(thread_url)))
        return redirect(url_for('secure_message_bp.view_conversation_list'))

    return render_template('secure-messages/conversation-view.html',
                           _theme='default',
                           form=form,
                           conversation=refined_conversation)


@secure_message_bp.route('/threads', methods=['GET'])
@jwt_authorization(request)
def view_conversation_list(session):
    party_id = session.get('party_id')
    logger.info("Getting conversation list", party_id=party_id)
    conversation = get_conversation_list()

    try:
        refined_conversation = [refine(message) for message in conversation]
    except KeyError as e:
        logger.exception("A key error occurred", party_id=party_id)
        raise ApiError(e)
    logger.info("Retrieving and refining conversation successful", party_id=party_id)

    return render_template('secure-messages/conversation-list.html',
                           _theme='default',
                           messages=refined_conversation)


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
