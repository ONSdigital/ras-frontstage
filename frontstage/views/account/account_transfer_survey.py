import json
import logging

from flask import flash, request
from flask import session as flask_session
from flask import url_for
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage import app
from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import party_controller, survey_controller
from frontstage.controllers.party_controller import (
    get_business_by_id,
    get_business_survey_enrolments_map,
    get_existing_pending_surveys,
    get_respondent_enrolments,
    get_surveys_to_transfer_map,
    register_pending_surveys,
)
from frontstage.exceptions.exceptions import TransferSurveyProcessError
from frontstage.models import (
    AccountSurveyShareRecipientEmailForm,
    ConfirmEmailChangeForm,
)
from frontstage.views.account import account_bp
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))

INVALID_SURVEY_TRANSFER_ERROR = (
    "You have reached the maximum amount of emails you can enroll on one or more surveys. "
    "Deselect the survey/s to continue or call 0300 1234 931 to discuss your options."
)

SELECT_A_SURVEY_ERROR = "You need to select a survey"


@account_bp.route("/transfer-surveys", methods=["GET"])
@jwt_authorization(request)
def transfer_surveys(_):
    flask_session.pop("surveys_to_transfer_map", None)
    flask_session.pop("transfer_survey_recipient_email_address", None)
    return redirect(url_for("account_bp.survey_selection"))


@account_bp.route("/transfer-surveys/survey-selection", methods=["GET", "POST"])
@jwt_authorization(request)
def survey_selection(session):
    error = None
    invalid_survey_shares = []

    if request.method == "POST":
        surveys_to_transfer_map, invalid_survey_shares = get_surveys_to_transfer_map(
            request.form.getlist("selected_surveys")
        )
        if surveys_to_transfer_map:
            if not invalid_survey_shares:
                flask_session["surveys_to_transfer_map"] = surveys_to_transfer_map
                return redirect(url_for("account_bp.transfer_survey_email_entry"))
            else:
                error = INVALID_SURVEY_TRANSFER_ERROR
        else:
            flask_session.pop("surveys_to_transfer", None)
            error = SELECT_A_SURVEY_ERROR

    party_id = session.get_party_id()
    respondent_enrolments = get_respondent_enrolments(party_id)

    return render_template(
        "surveys/surveys-transfer/survey-select.html",
        respondent_enrolments=respondent_enrolments,
        error=error,
        invalid_survey_shares=invalid_survey_shares,
    )


@account_bp.route("/transfer-surveys/recipient-email-address", methods=["GET", "POST"])
@jwt_authorization(request)
def transfer_survey_email_entry(session):
    form = AccountSurveyShareRecipientEmailForm(request.values)

    if request.method == "POST":
        if not form.validate():
            return render_template(
                "surveys/surveys-transfer/recipient-email-address.html", form=form, errors=form.errors
            )
        party_id = session.get_party_id()
        respondent_details = party_controller.get_respondent_party_by_id(party_id)

        if respondent_details["emailAddress"].lower() == form.data["email_address"].lower():
            errors = {"email_address": ["You can not transfer surveys to yourself."]}

            return render_template("surveys/surveys-transfer/recipient-email-address.html", form=form, errors=errors)

        flask_session["transfer_survey_recipient_email_address"] = form.data["email_address"]

        existing_pending_surveys = get_existing_pending_surveys(party_id)

        if existing_pending_surveys:
            duplicate_transfers = _get_duplicate_transfers(existing_pending_surveys, form.data["email_address"])
            if duplicate_transfers:
                business_survey_enrolments = get_business_survey_enrolments_map(party_id)
                errors = {
                    "email_address": [
                        _build_duplicate_transfer_error_message(duplicate_transfers, business_survey_enrolments)
                    ]
                }
                return render_template(
                    "surveys/surveys-transfer/recipient-email-address.html", form=form, errors=errors
                )

        return redirect(url_for("account_bp.send_transfer_instruction_get"))

    return render_template("surveys/surveys-transfer/recipient-email-address.html", form=form)


def _get_duplicate_transfers(existing_pending_surveys, email_address):
    duplicate_transfers = []
    for existing_pending_survey in existing_pending_surveys:
        if (
            _existing_pending_survey_is_in_selection(
                flask_session["surveys_to_transfer_map"],
                existing_pending_survey["business_id"],
                existing_pending_survey["survey_id"],
            )
            and existing_pending_survey["email_address"].lower() == email_address.lower()
        ):
            duplicate_transfers.append(
                {
                    "business_id": existing_pending_survey["business_id"],
                    "survey_id": existing_pending_survey["survey_id"],
                    "email_address": existing_pending_survey["email_address"].lower(),
                }
            )
    return duplicate_transfers


def _build_duplicate_transfer_error_message(duplicate_transfers, business_survey_enrolments):
    error_message = "You have already shared or transferred the following surveys to this email address. "
    error_message += "They have 72 hours to accept your request. "
    error_message += "<br /><br />If you have made an error then wait for the share/transfer to expire or contact us."
    error_message += "<ul>"
    for transfer in duplicate_transfers:
        business_name = business_survey_enrolments[transfer["business_id"]]["business_name"]
        survey_name = next(
            survey["long_name"]
            for survey in business_survey_enrolments[transfer["business_id"]]["surveys"]
            if survey["id"] == transfer["survey_id"]
        )
        error_message += "<li>" + business_name + " - " + survey_name + "</li>"
    error_message += "</ul>"
    return error_message


def _existing_pending_survey_is_in_selection(surveys_to_transfer_map, business_id, survey_id):
    if business_id in surveys_to_transfer_map:
        return survey_id in surveys_to_transfer_map[business_id]
    return False


@account_bp.route("/transfer-surveys/send-instruction", methods=["GET"])
@jwt_authorization(request)
def send_transfer_instruction_get(_):
    email = flask_session["transfer_survey_recipient_email_address"]
    surveys_to_be_transferred = {}
    surveys_to_transfer_map = flask_session["surveys_to_transfer_map"]

    for business_id, survey_ids in surveys_to_transfer_map.items():
        selected_business = get_business_by_id(business_id)
        surveys = []
        for survey_id in survey_ids:
            surveys.append(survey_controller.get_survey(app.config["SURVEY_URL"], app.config["BASIC_AUTH"], survey_id))

        surveys_to_be_transferred[selected_business[0]["id"]] = {
            "name": selected_business[0]["name"],
            "surveys": surveys,
        }
        flask_session["transferred_surveys"] = surveys_to_be_transferred
    return render_template(
        "surveys/surveys-transfer/send-instructions.html",
        email=email,
        surveys_to_be_transferred=surveys_to_be_transferred,
        form=ConfirmEmailChangeForm(),
    )


@account_bp.route("/transfer-surveys/send-instruction", methods=["POST"])
@jwt_authorization(request)
def send_transfer_instruction(session):
    form = ConfirmEmailChangeForm(request.values)
    email = flask_session["transfer_survey_recipient_email_address"]
    party_id = session.get_party_id()
    respondent_details = party_controller.get_respondent_party_by_id(party_id)

    if form["email_address"].data != email:
        raise TransferSurveyProcessError("Could not find email address in session")

    json_data = _build_payload(respondent_details["id"])
    response = register_pending_surveys(json_data, party_id)
    if response.status_code == 400:
        flash(
            "You have already shared or transferred these surveys with someone with this email address. They have 72 "
            "hours to accept your request. If you have made an error then wait for the share/transfer to expire or "
            "contact us.",
        )
        return redirect(url_for("account_bp.send_transfer_instruction_get"))
    return render_template(
        "surveys/surveys-transfer/instructions-sent.html",
        email=email,
    )


def _build_payload(respondent_id) -> json:
    email = flask_session["transfer_survey_recipient_email_address"]
    payload = {}
    pending_shares = []
    surveys_to_transfer_map = flask_session["surveys_to_transfer_map"]

    for business_id, survey_ids in surveys_to_transfer_map.items():
        for survey_id in survey_ids:
            pending_share = {
                "business_id": business_id,
                "survey_id": survey_id,
                "email_address": email,
                "shared_by": respondent_id,
            }
            pending_shares.append(pending_share)
    payload["pending_transfers"] = pending_shares
    return json.dumps(payload)
