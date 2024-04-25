import logging

from flask import flash, request, url_for
from markupsafe import Markup
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers.conversation_controller import (
    InvalidSecureMessagingForm,
    send_message,
)
from frontstage.views.surveys import surveys_bp
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))

option_template_url_mapping = {"my-survey-is-not-listed": "surveys/help/surveys-help-my-survey-is-not-listed.html"}
subject_text_mapping = {"my-survey-is-not-listed": "My survey is not listed"}

breadcrumb_surveys = {"text": "Surveys", "url": "/surveys/todo", "id": "b-item-1"}
breadcrumb_text_mapping = {
    "my-survey-is-not-listed": [
        breadcrumb_surveys,
        {"text": "My survey is not listed", "url": "/surveys/technical/my-survey-is-not-listed", "id": "b-item-2"},
    ],
}


@surveys_bp.route("/technical/<option>", methods=["GET"])
@jwt_authorization(request)
def get_technical_message_page_option(session, option):
    template = option_template_url_mapping.get(option, "Invalid template")
    return render_template(template, session=session, option=option)


@surveys_bp.route("/technical/send-message", methods=["GET"])
@jwt_authorization(request)
def get_send_help_technical_message_page(session):
    """Gets the send message page"""
    option = request.args.get("option", None)
    subject = subject_text_mapping.get(option, None)
    breadcrumbs = breadcrumb_text_mapping.get(option, None)
    return render_template(
        "secure-messages/help/secure-message-send-technical-messages-view.html",
        session=session,
        option=option,
        subject=subject,
        breadcrumbs=breadcrumbs,
    )


@surveys_bp.route("/technical/send-message", methods=["POST"])
@jwt_authorization(request)
def send_help_technical_message(session):
    """Sends secure message for the help pages"""
    option = request.args.get("option", None)
    subject = subject_text_mapping.get(option)
    party_id = session.get_party_id()

    try:
        msg_id = send_message(request.form, party_id, "dd", subject)
    except InvalidSecureMessagingForm as e:
        flash(e.errors["body"][0])
        return redirect(url_for("surveys_bp.get_send_help_technical_message_page", option=option))

    thread_url = url_for("secure_message_bp.view_conversation", thread_id=msg_id) + "#latest-message"
    flash(Markup(f"Message sent. <a href={thread_url}>View Message</a>"))
    return redirect(url_for("surveys_bp.get_survey_list", tag="todo"))
