import logging
from distutils.util import strtobool

from flask import Markup, flash, json, redirect, render_template, request, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.authorisation import jwt_authorization
from frontstage.common.message_helper import from_internal, refine
from frontstage.controllers.conversation_controller import (
    get_conversation,
    get_conversation_list,
    get_message_count_from_api,
    remove_unread_label,
    send_message,
    try_message_count_from_session,
)
from frontstage.controllers.survey_controller import get_survey
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import SecureMessagingForm
from frontstage.views.secure_messaging import secure_message_bp

logger = wrap_logger(logging.getLogger(__name__))


@secure_message_bp.route("/threads/<thread_id>", methods=["GET", "POST"])
@jwt_authorization(request)
def view_conversation(session, thread_id):
    """Endpoint to view conversations by thread_id"""
    party_id = session.get_party_id()
    logger.info("Getting conversation", thread_id=thread_id, party_id=party_id)
    conversation = get_conversation(thread_id)
    # secure message will send category in case the conversation is technical or miscellaneous
    is_survey_category = (
        False if "category" in conversation and conversation["category"] in ["TECHNICAL", "MISC"] else True
    )
    # sets appropriate message category
    category = "SURVEY" if is_survey_category else conversation["category"]
    logger.info("Successfully retrieved conversation", thread_id=thread_id, party_id=party_id)
    try:
        refined_conversation = [refine(message) for message in reversed(conversation["messages"])]
    except KeyError:
        logger.error("Message is missing important data", thread_id=thread_id, party_id=party_id)
        raise

    if refined_conversation[-1]["unread"]:
        remove_unread_label(refined_conversation[-1]["message_id"])

    form = SecureMessagingForm(request.form)
    form.subject.data = refined_conversation[0].get("subject")

    if not conversation["is_closed"]:
        if form.validate_on_submit():
            logger.info("Sending message", thread_id=thread_id, party_id=party_id)
            msg_to = get_msg_to(refined_conversation)
            if is_survey_category:
                send_message(_get_message_json(form, refined_conversation[0], msg_to=msg_to, msg_from=party_id))
            else:
                send_message(
                    _get_non_survey_message_json(
                        form, refined_conversation[0], msg_to=msg_to, msg_from=party_id, category=category
                    )
                )
            logger.info("Successfully sent message", thread_id=thread_id, party_id=party_id)
            thread_url = url_for("secure_message_bp.view_conversation", thread_id=thread_id) + "#latest-message"
            flash(Markup(f"Message sent. <a href={thread_url}>View Message</a>"))
            return redirect(url_for("secure_message_bp.view_conversation_list"))

    unread_message_count = {"unread_message_count": get_message_count_from_api(session)}
    survey_name = None
    business_name = None
    if is_survey_category:
        try:
            survey_name = get_survey(
                app.config["SURVEY_URL"], app.config["BASIC_AUTH"], refined_conversation[-1]["survey_id"]
            ).get("longName")
        except ApiError as exc:
            logger.info("Failed to get survey name, setting to None", status_code=exc.status_code)
        try:
            business_name = conversation["messages"][-1]["@business_details"]["name"]
        except (KeyError, TypeError):
            logger.info("Failed to get business name, setting to None")

    return render_template(
        "secure-messages/conversation-view.html",
        form=form,
        conversation=refined_conversation,
        conversation_data=conversation,
        unread_message_count=unread_message_count,
        survey_name=survey_name,
        business_name=business_name,
        category=category,
    )


@secure_message_bp.route("/threads", methods=["GET"])
@jwt_authorization(request)
def view_conversation_list(session):
    party_id = session.get_party_id()
    logger.info("Getting conversation list", party_id=party_id)
    is_closed = request.args.get("is_closed", default="false")
    params = {"is_closed": is_closed}

    conversation = get_conversation_list(params=params)

    try:
        refined_conversation = [refine(message) for message in conversation]
    except KeyError:
        logger.error("A key error occurred", party_id=party_id)
        raise
    logger.info("Retrieving and refining conversation successful", party_id=party_id)
    unread_message_count = {"unread_message_count": try_message_count_from_session(session)}
    return render_template(
        "secure-messages/conversation-list.html",
        messages=refined_conversation,
        is_closed=strtobool(is_closed),
        unread_message_count=unread_message_count,
    )


def _get_message_json(form, first_message_in_conversation, msg_to, msg_from):
    return json.dumps(
        {
            "msg_from": msg_from,
            "msg_to": msg_to,
            "subject": form.subject.data,
            "body": form.body.data,
            "thread_id": first_message_in_conversation["thread_id"],
            "survey_id": first_message_in_conversation.get("survey_id", "No Survey"),
            "business_id": first_message_in_conversation.get("ru_ref", "No Business"),
        }
    )


def _get_non_survey_message_json(form, first_message_in_conversation, msg_to, msg_from, category):
    return json.dumps(
        {
            "msg_from": msg_from,
            "msg_to": msg_to,
            "subject": form.subject.data,
            "body": form.body.data,
            "thread_id": first_message_in_conversation["thread_id"],
            "category": category,
        }
    )


def get_msg_to(conversation):
    """Walks the conversation from latest sent message to first and looks for the latest message sent from internal.
    Uses that as the to , if none found then defaults to group"""
    for message in reversed(conversation):
        if from_internal(message):
            return [message["internal_user"]]
    return ["GROUP"]
