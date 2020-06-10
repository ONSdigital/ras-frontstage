import logging
from distutils.util import strtobool

from flask import json, flash, Markup, render_template, redirect, request, url_for
from structlog import wrap_logger

from frontstage.common.authorisation import jwt_authorization
from frontstage.common.message_helper import from_internal, refine
from frontstage.controllers.conversation_controller import get_conversation, get_conversation_list, \
    remove_unread_label, send_message, try_message_count_from_session, get_message_count_from_api
from frontstage.models import SecureMessagingForm
from frontstage.views.secure_messaging import secure_message_bp


logger = wrap_logger(logging.getLogger(__name__))


@secure_message_bp.route('/thread/<thread_id>', methods=['GET', 'POST'])
@secure_message_bp.route('/threads/<thread_id>', methods=['GET', 'POST'])
@jwt_authorization(request)
def view_conversation(session, thread_id):
    """Endpoint to view conversations by thread_id

    NOTE: /thread/<thread_id> endpoint is there for compatability reasons.  All new emails use /threads/<thread_id>.
    From September 2019 onwards, it should be safe to remove the /thread endpoint (just check the analytics to make
    sure that it's a very small number of people trying to hit it first!).
    """
    party_id = session.get_party_id()
    logger.info("Getting conversation", thread_id=thread_id, party_id=party_id)
    # TODO, do we really want to do a GET every time, even if we're POSTing? Rops does it this
    # way so we can get it working, then get it right.
    conversation = get_conversation(thread_id)
    logger.info('Successfully retrieved conversation', thread_id=thread_id, party_id=party_id)
    try:
        refined_conversation = [refine(message) for message in reversed(conversation['messages'])]
    except KeyError as e:
        logger.error('Message is missing important data', thread_id=thread_id, party_id=party_id)
        raise e

    if refined_conversation[-1]['unread']:
        remove_unread_label(refined_conversation[-1]['message_id'])

    form = SecureMessagingForm(request.form)
    form.subject.data = refined_conversation[0].get('subject')

    if not conversation['is_closed']:
        if form.validate_on_submit():
            logger.info("Sending message", thread_id=thread_id, party_id=party_id)
            msg_to = get_msg_to(refined_conversation)
            send_message(_get_message_json(form, refined_conversation[0], msg_to=msg_to, msg_from=party_id))
            logger.info("Successfully sent message", thread_id=thread_id, party_id=party_id)
            thread_url = url_for("secure_message_bp.view_conversation", thread_id=thread_id) + "#latest-message"
            flash(Markup('Message sent. <a href={}>View Message</a>'.format(thread_url)))
            return redirect(url_for('secure_message_bp.view_conversation_list'))

    unread_message_count = {'unread_message_count': get_message_count_from_api(session)}

    return render_template('secure-messages/conversation-view.html',
                           form=form,
                           conversation=refined_conversation,
                           conversation_data=conversation,
                           unread_message_count=unread_message_count)


@secure_message_bp.route('/threads', methods=['GET'])
@jwt_authorization(request)
def view_conversation_list(session):
    party_id = session.get_party_id()
    logger.info('Getting conversation list', party_id=party_id)
    is_closed = request.args.get('is_closed', default='false')
    params = {'is_closed': is_closed}

    conversation = get_conversation_list(params=params)

    try:
        refined_conversation = [refine(message) for message in conversation]
    except KeyError as e:
        logger.error('A key error occurred', party_id=party_id)
        raise e
    logger.info('Retrieving and refining conversation successful', party_id=party_id)
    unread_message_count = {'unread_message_count': try_message_count_from_session(session)}
    return render_template('secure-messages/conversation-list.html',
                           messages=refined_conversation,
                           is_closed=strtobool(is_closed),
                           unread_message_count=unread_message_count)


def _get_message_json(form, first_message_in_conversation, msg_to, msg_from):

    return json.dumps({
        'msg_from': msg_from,
        'msg_to': msg_to,
        'subject': form.subject.data,
        'body': form.body.data,
        'thread_id': first_message_in_conversation['thread_id'],
        'collection_case': "",
        'survey': first_message_in_conversation['survey_id'],
        'business_id': first_message_in_conversation['ru_ref']})


def get_msg_to(conversation):
    """Walks the conversation from latest sent message to first and looks for the latest message sent from internal.
    Uses that as the to , if none found then defaults to group """
    for message in reversed(conversation):
        if from_internal(message):
            return [message['internal_user']]
    return ['GROUP']
