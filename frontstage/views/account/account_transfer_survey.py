import json
import logging
from datetime import datetime, timezone

from flask import flash, render_template, request
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
    get_surveys_listed_against_party_and_business_id,
    get_user_count_registered_against_business_and_survey,
    register_pending_shares,
)
from frontstage.exceptions.exceptions import ShareSurveyProcessError
from frontstage.models import (
    AccountSurveySelectBusinessForm,
    AccountSurveyShareRecipientEmailForm,
    ConfirmEmailChangeForm,
)
from frontstage.views.account import account_bp

logger = wrap_logger(logging.getLogger(__name__))


@account_bp.route("/transfer-surveys", methods=["GET"])
@jwt_authorization(request)
def transfer_survey_overview(session):
    # 'transfer_survey_data' holds business and surveys selected for share
    flask_session.pop("transfer_survey_data", None)
    # 'transfer_survey_recipient_email_address' holds the recipient email address
    flask_session.pop("transfer_survey_recipient_email_address", None)
    # 'validation_failure_transfer_surveys_list' holds list of surveys which has failed max share validation
    # this will be used to show red mark on UI
    flask_session.pop("validation_failure_transfer_surveys_list", None)
    # 'transfer_surveys_selected_list' holds list of surveys selected by user so that its checked in case of any error
    flask_session.pop("transfer_surveys_selected_list", None)
    return render_template("surveys/surveys-transfer/overview.html", expires_at=session.get_formatted_expires_in())


@account_bp.route("/transfer-surveys/business-selection", methods=["GET"])
@jwt_authorization(request)
def transfer_survey_business_select(session):
    flask_session.pop("transfer_survey_recipient_email_address", None)
    flask_session.pop("validation_failure_transfer_surveys_list", None)
    flask_session.pop("transfer_surveys_selected_list", None)
    form = AccountSurveySelectBusinessForm(request.values)
    party_id = session.get_party_id()
    businesses = get_list_of_business_for_party(party_id)
    return render_template("surveys/surveys-transfer/business-select.html", businesses=businesses, form=form,
                           expires_at=session.get_formatted_expires_in())


@account_bp.route("/transfer-surveys/business-selection", methods=["POST"])
@jwt_authorization(request)
def transfer_survey_post_business_select(session):
    flask_session.pop("transfer_survey_data", None)
    transfer_survey_business_selected = request.form.getlist("checkbox-answer")
    if len(transfer_survey_business_selected) == 0:
        flash("Select an answer")
        return redirect(url_for("account_bp.transfer_survey_business_select"))
    flask_session["transfer_survey_data"] = {k: [] for k in transfer_survey_business_selected}
    return redirect(url_for("account_bp.transfer_survey_survey_select"))


@account_bp.route("/transfer-surveys/survey-selection", methods=["GET"])
@jwt_authorization(request)
def transfer_survey_survey_select(session):
    party_id = session.get_party_id()
    transfer_dict = {}
    for business_id in flask_session["transfer_survey_data"]:
        selected_business = get_business_by_id(business_id)
        surveys = get_surveys_listed_against_party_and_business_id(business_id, party_id)
        transfer_dict[selected_business[0]["id"]] = {
            "name": selected_business[0]["name"],
            "surveys": surveys,
        }
    error = request.args.get("error", "")
    failed_surveys_list = flask_session.get("validation_failure_transfer_surveys_list")
    selected_survey_list = flask_session.get("transfer_surveys_selected_list")
    return render_template(
        "surveys/surveys-transfer/survey-select.html",
        transfer_dict=transfer_dict,
        error=error,
        failed_surveys_list=failed_surveys_list if failed_surveys_list is not None else [],
        selected_survey_list=selected_survey_list if selected_survey_list is not None else [],
        expires_at=session.get_formatted_expires_in(),
    )


def validate_max_transfer_survey(business_id: str, transfer_survey_surveys_selected: list):
    """
    This is a validation for maximum user reached against a survey for transfer
    param: business_id : business id str
    param: transfer_survey_surveys_selected : selected business list
    return:boolean
    """
    is_valid = True
    failed_surveys_list = []
    for survey_selected in transfer_survey_surveys_selected:
        logger.info(
            "Getting count of users registered against business and survey",
            business_id=business_id,
            survey_id=survey_selected,
        )
        user_count = get_user_count_registered_against_business_and_survey(business_id, survey_selected, True)
        if user_count > (app.config["MAX_SHARED_SURVEY"] + 1):
            is_valid = False
            failed_surveys_list.append(survey_selected)
    flask_session["validation_failure_transfer_surveys_list"] = failed_surveys_list
    return is_valid


def get_selected_businesses():
    """
    This function returns list of business objects against selected business_ids in flask session
    return: list
    """
    selected_businesses = []
    for business_id in flask_session["transfer_survey_data"]:
        selected_businesses.append(get_business_by_id(business_id))
    return selected_businesses


def set_surveys_selected_list(selected_businesses, form):
    """
    This function sets the flask session key 'transfer_surveys_selected_list' with users selection
    param: selected_businesses : list of businesses
    param: form : request form
    return:None
    """
    flask_session.pop("transfer_surveys_selected_list", None)
    transfer_surveys_selected_list = []
    for business in selected_businesses:
        transfer_surveys_selected_list.append(form.getlist(business[0]["id"]))
    flask_session["transfer_surveys_selected_list"] = [
        item for sublist in transfer_surveys_selected_list for item in sublist
    ]


def is_surveys_selected_against_selected_businesses(selected_businesses, form):
    """
    This function validates if all selected business have survey selection and creates flash messages in case of
    validation failures
    param: selected_businesses : list of businesses
    param: form : request form
    return:boolean
    """
    surveys_not_selected = False
    for business in selected_businesses:
        transfer_surveys_selected_against_business = form.getlist(business[0]["id"])
        if len(transfer_surveys_selected_against_business) == 0:
            flash("Select an answer", business[0]["id"])
            surveys_not_selected = True
    return surveys_not_selected


def is_max_transfer_survey_exceeded(selected_businesses, form):
    """
    This function validates if selected surveys has not exceeded max share and creates flash messaged in case of
    validation failures
    param: selected_businesses : list of businesses
    param: form : request form
    return:boolean
    """
    is_max_transfer_survey = False
    for business in selected_businesses:
        transfer_surveys_selected_against_business = form.getlist(business[0]["id"])
        if not validate_max_transfer_survey(business[0]["id"], transfer_surveys_selected_against_business):
            flash(
                "You have reached the maximum amount of emails you can enroll on one or more surveys",
                business[0]["id"],
            )
            is_max_transfer_survey = True
    return is_max_transfer_survey


@account_bp.route("/transfer-surveys/survey-selection", methods=["POST"])
@jwt_authorization(request)
def transfer_survey_post_survey_select(session):
    share_dictionary_copy = flask_session["transfer_survey_data"]
    flask_session.pop("validation_failure_transfer_surveys_list", None)
    selected_businesses = get_selected_businesses()
    set_surveys_selected_list(selected_businesses, request.form)
    # this is to accommodate multiple business survey selection error messages on UI.
    # the validation needs to be carried out in two steps one all the surveys are selected
    # second max share survey validation
    if is_surveys_selected_against_selected_businesses(selected_businesses, request.form):
        return redirect(url_for("account_bp.transfer_survey_survey_select", error="surveys_not_selected"))
    if is_max_transfer_survey_exceeded(selected_businesses, request.form):
        return redirect(url_for("account_bp.transfer_survey_survey_select", error="max_transfer_survey_exceeded"))

    for business in selected_businesses:
        transfer_surveys_selected_against_business = request.form.getlist(business[0]["id"])
        share_dictionary_copy[business[0]["id"]] = transfer_surveys_selected_against_business

    flask_session.pop("validation_failure_transfer_surveys_list", None)
    flask_session.pop("transfer_surveys_selected_list", None)
    flask_session.pop("share", None)
    flask_session["transfer_survey_data"] = share_dictionary_copy
    return redirect(url_for("account_bp.transfer_survey_email_entry"))


@account_bp.route("/transfer-surveys/recipient-email-address", methods=["GET"])
@jwt_authorization(request)
def transfer_survey_email_entry(session):
    form = AccountSurveyShareRecipientEmailForm(request.values)
    flask_session["transfer_survey_recipient_email_address"] = None
    return render_template("surveys/surveys-transfer/recipient-email-address.html", form=form, errors=form.errors,
                           expires_at=session.get_formatted_expires_in())


@account_bp.route("/transfer-surveys/recipient-email-address", methods=["POST"])
@jwt_authorization(request)
def transfer_survey_post_email_entry(session):
    form = AccountSurveyShareRecipientEmailForm(request.values)
    party_id = session.get_party_id()
    respondent_details = party_controller.get_respondent_party_by_id(party_id)
    expires_at = session.get_formatted_expires_in()
    if not form.validate():
        errors = form.errors
        return render_template("surveys/surveys-transfer/recipient-email-address.html", form=form, errors=errors,
                               expires_at=expires_at)

    if "emailAddress" in respondent_details:
        if respondent_details["emailAddress"].lower() == form.data["email_address"].lower():
            errors = {"email_address": ["You can not transfer surveys to yourself."]}
            return render_template("surveys/surveys-transfer/recipient-email-address.html", form=form, errors=errors,
                                   expires_at=expires_at)
    flask_session["transfer_survey_recipient_email_address"] = form.data["email_address"]
    return redirect(url_for("account_bp.send_transfer_instruction_get"))


@account_bp.route("/transfer-surveys/send-instruction", methods=["GET"])
@jwt_authorization(request)
def send_transfer_instruction_get(session):
    email = flask_session["transfer_survey_recipient_email_address"]
    share_dict = {}
    for business_id in flask_session["transfer_survey_data"]:
        selected_business = get_business_by_id(business_id)
        surveys = []
        for survey_id in flask_session["transfer_survey_data"][business_id]:
            surveys.append(survey_controller.get_survey(app.config["SURVEY_URL"], app.config["BASIC_AUTH"], survey_id))
        share_dict[selected_business[0]["id"]] = {
            "name": selected_business[0]["name"],
            "surveys": surveys,
        }
    return render_template(
        "surveys/surveys-transfer/send-instructions.html",
        email=email,
        share_dict=share_dict,
        form=ConfirmEmailChangeForm(),
        expires_at=session.get_formatted_expires_in(),
    )


def build_payload(respondent_id):
    """
    This method builds payload required for the party endpoint to register new pending surveys.
    payload example:
    {  pending_transfers: [{
        "business_id": "business_id"
        "survey_id": "survey_id",
        "email_address": "email_address",
        "shared_by": "party_uuid"
    },
    {
        "business_id": "business_id":
        "survey_id": "survey_id",
        "email_address": "email_address",
        "shared_by": "party_uuid"
    }]
    }
    """
    email = flask_session["transfer_survey_recipient_email_address"]
    payload = {}
    pending_shares = []
    share_dictionary = flask_session["transfer_survey_data"]
    for business_id in share_dictionary:
        for survey in share_dictionary[business_id]:
            pending_share = {
                "business_id": business_id,
                "survey_id": survey,
                "email_address": email,
                "shared_by": respondent_id,
            }
            pending_shares.append(pending_share)
    payload["pending_transfers"] = pending_shares
    return json.dumps(payload)


@account_bp.route("/transfer-surveys/send-instruction", methods=["POST"])
@jwt_authorization(request)
def send_transfer_instruction(session):
    form = ConfirmEmailChangeForm(request.values)
    email = flask_session["transfer_survey_recipient_email_address"]
    party_id = session.get_party_id()
    respondent_details = party_controller.get_respondent_party_by_id(party_id)
    if form["email_address"].data != email:
        raise ShareSurveyProcessError("Process failed due to session error")
    json_data = build_payload(respondent_details["id"])
    response = register_pending_shares(json_data)
    if response.status_code == 400:
        flash(
            "You have already shared or transferred these surveys with someone with this email address. They have 72 "
            "hours to accept your request. If you have made an error then wait for the share/transfer to expire or "
            "contact us.",
        )
        return redirect(url_for("account_bp.send_transfer_instruction_get"))
    return render_template("surveys/surveys-transfer/almost-done.html", expires_at=session.get_formatted_expires_in(),)


@account_bp.route("/transfer-surveys/done", methods=["GET"])
@jwt_authorization(request)
def transfer_survey_done(session):
    flask_session.pop("share", None)
    flask_session.pop("transfer_survey_recipient_email_address", None)
    return redirect(url_for("surveys_bp.get_survey_list", tag="todo"))
