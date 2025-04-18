import logging
import urllib.parse as urlparse

from flask import Blueprint, flash, request, url_for
from markupsafe import Markup
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage.common.authorisation import is_authorization, jwt_authorization
from frontstage.controllers.conversation_controller import (
    NOT_SURVEY_RELATED,
    InvalidSecureMessagingForm,
    secure_message_enrolment_options,
    secure_message_organisation_options,
    send_secure_message,
)
from frontstage.controllers.party_controller import get_respondent_enrolments
from frontstage.models import OrganisationForm, SecureMessagingForm
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))

contact_us_bp = Blueprint("contact_us_bp", __name__, static_folder="static", template_folder="templates")


@contact_us_bp.route("/", methods=["GET"])
def contact_us():
    return render_template("contact-us.html", authorization=is_authorization())


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

    url_parts = urlparse.urlparse(request.url)
    url_business_id = urlparse.parse_qs(url_parts.query).get("business_id")
    payload = {"business_id": url_business_id[0]} if url_business_id else {}

    respondent_enrolments = get_respondent_enrolments(session.get_party_id(), payload=payload)

    if len(respondent_enrolments) > 1:
        return redirect(url_for("contact_us_bp.select_organisation"))

    enrolment_options = secure_message_enrolment_options(respondent_enrolments, secure_message_form)
    back_url = (
        url_for("contact_us_bp.select_organisation")
        if url_business_id
        else url_for("surveys_bp.get_survey_list", tag="todo")
    )

    return render_template(
        "secure-messages/help/secure-message-send-messages-view.html",
        enrolment_options=enrolment_options,
        back_url=back_url,
        form=secure_message_form,
        errors=errors,
    )


@contact_us_bp.route("/select-organisation", methods=["GET", "POST"])
@jwt_authorization(request)
def select_organisation(session) -> str:
    organisation_form = OrganisationForm(request.form)

    if request.method == "POST" and organisation_form.validate():
        return redirect(url_for("contact_us_bp.send_message", business_id=organisation_form.business_id.data))

    respondent_enrolments = get_respondent_enrolments(session.get_party_id())

    business_details = []
    for enrolment in respondent_enrolments:
        business_details.append({"business_id": enrolment["business_id"], "business_name": enrolment["business_name"]})

    organisation_options = secure_message_organisation_options(business_details)

    return render_template(
        "secure-messages/help/secure-message-select-organisation.html",
        organisation_options=organisation_options,
        back_url=url_for("surveys_bp.get_survey_list", tag="todo"),
        error=_errors(organisation_form.errors),
    )


def _errors(errors: dict) -> dict:
    errors_dict = {}
    for key, value in errors.items():
        errors_dict[key] = {"text": value[0], "id": f"{key}_error"}
    return errors_dict
