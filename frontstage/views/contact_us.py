import logging

from flask import Blueprint, flash, request, url_for
from markupsafe import Markup
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers.conversation_controller import (
    NOT_SURVEY_RELATED,
    InvalidSecureMessagingForm,
    secure_message_enrolment_options,
    send_secure_message,
)
from frontstage.models import SecureMessagingForm
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))

contact_us_bp = Blueprint("contact_us_bp", __name__, static_folder="static", template_folder="templates")


@contact_us_bp.route("/", methods=["GET"])
def contact_us():
    return render_template("contact-us.html")


@contact_us_bp.route("/send-message", methods=["GET", "POST"])
@jwt_authorization(request)
def send_message(session) -> str:
    secure_message_form = SecureMessagingForm(request.form)
    errors = {}
    if request.method == "POST":
        secure_message_form.party_id = session.get_party_id()
        secure_message_form.category = "TECHNICAL" if request.form.get("survey_id") == NOT_SURVEY_RELATED else "SURVEY"

        try:
            msg_id = send_secure_message(secure_message_form)
            thread_url = url_for("secure_message_bp.view_conversation", thread_id=msg_id) + "#latest-message"
            flash(
                Markup(
                    f"Your message has been sent, a request can take up to 5 working days <a href={thread_url}>View Message</a>"
                )
            )
            return redirect(url_for("surveys_bp.get_survey_list", tag="todo"))
        except InvalidSecureMessagingForm as e:
            errors = _errors(e.errors)

    enrolment_options = secure_message_enrolment_options(
        session.get_party_id(),
        secure_message_form,
    )
    return render_template(
        "secure-messages/help/secure-message-send-messages-view.html",
        enrolment_options=enrolment_options,
        form=secure_message_form,
        errors=errors,
    )


def _errors(errors: dict) -> dict:
    errors_dict = {}
    for key, value in errors.items():
        errors_dict[key] = {"text": value[0], "id": f"{key}_error"}
    return errors_dict
