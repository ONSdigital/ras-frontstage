import logging

from flask import flash, request, url_for
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage import app
from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import party_controller, survey_controller
from frontstage.controllers.party_controller import get_business_by_id
from frontstage.exceptions.exceptions import ApiError
from frontstage.views.account import account_bp
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))


@account_bp.route("/share-surveys/accept-share-surveys/<token>", methods=["GET"])
def get_share_survey_summary(token):
    """
    Endpoint to verify token and retrieve the summary page
    :param token: share survey token
    :type token: str
    """
    logger.info("Getting share survey summary", token=token)
    try:
        response = party_controller.verify_pending_survey_token(token)
        pending_share_surveys = response.json()
        share_dict = {}
        distinct_businesses = set()
        batch_number = pending_share_surveys[0]["batch_no"]
        originator_party = party_controller.get_respondent_party_by_id(pending_share_surveys[0]["shared_by"])
        shared_by = originator_party["emailAddress"]
        for pending_share_survey in pending_share_surveys:
            distinct_businesses.add(pending_share_survey["business_id"])
        for business_id in distinct_businesses:
            business_surveys = []
            for pending_share_survey in pending_share_surveys:
                if pending_share_survey["business_id"] == business_id:
                    business_surveys.append(
                        survey_controller.get_survey(
                            app.config["SURVEY_URL"], app.config["BASIC_AUTH"], pending_share_survey["survey_id"]
                        )
                    )
            selected_business = get_business_by_id(business_id)
            share_dict[selected_business[0]["id"]] = {
                "name": selected_business[0]["name"],
                "trading_as": selected_business[0]["trading_as"],
                "surveys": business_surveys,
            }
        return render_template(
            "surveys/surveys-share/summary.html", share_dict=share_dict, batch_no=batch_number, shared_by=shared_by
        )

    except ApiError as exc:
        # Handle api errors
        if exc.status_code == 409:
            logger.info(
                "Expired share survey email verification token",
                token=token,
                api_url=exc.url,
                api_status_code=exc.status_code,
            )
            return render_template("surveys/surveys-link-expired.html", is_transfer=False)
        elif exc.status_code == 404:
            logger.warning(
                "Unrecognised share survey email verification token",
                token=token,
                api_url=exc.url,
                api_status_code=exc.status_code,
            )
            return render_template("surveys/surveys-link-not-valid.html", is_transfer=False)
        else:
            logger.info(
                "Failed to verify share survey email", token=token, api_url=exc.url, api_status_code=exc.status_code
            )
            raise exc


@account_bp.route("/confirm-share-surveys/<batch>", methods=["GET"])
def accept_share_surveys(batch):
    """
    Accept endpoint when a share survey summary is accepted
    :param batch: batch number
    :type batch: str
    """
    logger.info("Attempting to get batch number", batch_number=batch)
    try:
        response = party_controller.get_pending_surveys_batch_number(batch)
        is_existing_user = _is_existing_account(response.json()[0]["email_address"])
    except ApiError as exc:
        logger.error("Failed to confirm share survey", status=exc.status_code, batch_number=batch)
        raise exc
    if is_existing_user:
        return redirect(url_for("account_bp.accept_share_surveys_existing_account", batch=batch))
    return redirect(
        url_for(
            "register_bp.pending_surveys_register_enter_your_details",
            batch_no=batch,
            email=response.json()[0]["email_address"],
            is_transfer=False,
        )
    )


@account_bp.route("/confirm-share-surveys/<batch>/existing-account", methods=["GET"])
@jwt_authorization(request)
def accept_share_surveys_existing_account(session, batch):
    """
    Accept redirect endpoint for accepting share surveys for existing account
    :param session:
    :type session:
    :param batch: batch number
    :type batch: str
    """
    logger.info("Attempting to confirm share surveys for existing account", batch_number=batch)
    party_id = session.get_party_id()
    respondent_details = party_controller.get_respondent_party_by_id(party_id)
    response = party_controller.get_pending_surveys_batch_number(batch)
    if respondent_details["emailAddress"].lower() != response.json()[0]["email_address"].lower():
        logger.warning("The user has entered invalid login for share survey.")
        flash("Invalid share survey login. This share survey is not assigned to you.", "error")
        return redirect(url_for("surveys_bp.get_survey_list", tag="todo"))
    try:
        party_controller.confirm_pending_survey(batch)
    except ApiError as exc:
        logger.error("Failed to confirm share survey for existing account", status=exc.status_code, batch_number=batch)
        raise exc
    logger.info("Successfully completed share survey for existing account", batch_number=batch)
    return render_template("surveys/surveys-share/share-survey-complete-thank-you.html", session=session)


def _is_existing_account(respondent_email):
    """
    Checks if the respondent already exists against the email address provided
    :param respondent_email: email of the respondent
    :type respondent_email: str
    :return: returns true if account already registered
    :rtype: bool
    """
    respondent = party_controller.get_respondent_by_email(respondent_email)
    if not respondent:
        return False
    return True
