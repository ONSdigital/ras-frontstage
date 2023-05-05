import json
import logging
from datetime import datetime, timezone

from flask import flash, render_template, request, url_for
from markupsafe import Markup
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import conversation_controller
from frontstage.models import SecureMessagingForm
from frontstage.views.surveys import surveys_bp

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
    return render_template(template, option=option)


@surveys_bp.route("/technical/send-message", methods=["GET"])
@jwt_authorization(request)
def get_send_help_technical_message_page(session):
    """Gets the send message page"""
    option = request.args.get("option", None)
    subject = subject_text_mapping.get(option, None)
    breadcrumbs = breadcrumb_text_mapping.get(option, None)
    return render_template(
        "secure-messages/help/secure-message-send-technical-messages-view.html",
        option=option,
        subject=subject,
        breadcrumbs=breadcrumbs,
        expires_at=session.get_formatted_expires_in(),
    )


@surveys_bp.route("/technical/send-message", methods=["POST"])
@jwt_authorization(request)
def send_help_technical_message(session):
    """Sends secure message for the help pages"""
    form = SecureMessagingForm(request.form)
    option = request.args.get("option", None)
    if not form.validate():
        flash(form.errors["body"][0])
        return redirect(url_for("surveys_bp.get_send_help_technical_message_page", option=option))
    else:
        subject = subject_text_mapping.get(option)
        party_id = session.get_party_id()
        logger.info("Form validation successful", party_id=party_id)

        sent_message = _send_new_message(subject, party_id)
        thread_url = (
            url_for("secure_message_bp.view_conversation", thread_id=sent_message["thread_id"]) + "#latest-message"
        )
        flash(Markup(f"Message sent. <a href={thread_url}>View Message</a>"))
        return redirect(url_for("surveys_bp.get_survey_list", tag="todo"))


def _send_new_message(subject, party_id):
    logger.info("Attempting to send technical message", party_id=party_id)
    form = SecureMessagingForm(request.form)
    message_json = {
        "msg_from": party_id,
        "msg_to": ["GROUP"],
        "subject": subject,
        "body": form["body"].data,
        "thread_id": form["thread_id"].data,
        "category": "TECHNICAL",
    }

    response = conversation_controller.send_message(json.dumps(message_json))

    logger.info("Secure message sent successfully", message_id=response["msg_id"], party_id=party_id)
    return response
