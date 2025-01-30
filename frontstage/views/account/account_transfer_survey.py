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
    get_list_of_business_for_party,
    get_respondent_enrolments,
    get_user_count_registered_against_business_and_survey,
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
        surveys_to_transfer_map, invalid_survey_shares = _create_surveys_to_transfer_map(
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
    businesses = get_list_of_business_for_party(party_id)
    business_survey_enrolments = []

    for business in businesses:
        survey_enrolments = _survey_enrolments_for_business_id(business["id"], party_id)
        business_survey_enrolments.append(
            {
                "business_name": business["name"],
                "business_id": business["id"],
                "business_ref": business["sampleUnitRef"],
                "surveys": survey_enrolments,
            }
        )

    return render_template(
        "surveys/surveys-transfer/survey-select.html",
        business_survey_enrolments=business_survey_enrolments,
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
        return redirect(url_for("account_bp.send_transfer_instruction_get"))

    return render_template("surveys/surveys-transfer/recipient-email-address.html", form=form)


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


def _create_surveys_to_transfer_map(selected_surveys):
    """
    creates a map of business ids to survey_ids that are to be transferred and whether they are valid
    """
    business_survey_map = {}
    invalid_survey_transfers = []

    for survey in selected_surveys:
        json_survey = json.loads(survey.replace("'", '"'))
        business_id = json_survey["business_id"]
        survey_id = json_survey["survey_id"]
        business_survey_map.setdefault(business_id, []).append(survey_id)
        _can_survey_be_transferred(business_id, survey_id, invalid_survey_transfers)

    return business_survey_map, invalid_survey_transfers


def _can_survey_be_transferred(business_id, survey_id, invalid_survey_transfers):
    count = get_user_count_registered_against_business_and_survey(business_id, survey_id, True)
    if count > (app.config["MAX_SHARED_SURVEY"] + 1):
        invalid_survey_transfers.append(business_id)


def _survey_enrolments_for_business_id(business_id: str, party_id: str) -> list:
    """
    returns the survey enrolments for a business_id and their current state
    """
    surveys_to_transfer = flask_session.get("surveys_to_transfer_map", {}).get(business_id, {})
    respondent_enrolments = get_respondent_enrolments(party_id, {"business_id": business_id})
    surveys = []

    for enrolment in respondent_enrolments:
        survey_id = enrolment["survey_details"]["id"]
        surveys.append(
            {
                "survey_details": enrolment["survey_details"],
                "selected": True if survey_id in surveys_to_transfer else False,
            }
        )
    return surveys


def _build_payload(respondent_id):
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
