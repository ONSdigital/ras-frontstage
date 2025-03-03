import logging

from flask import flash, request, url_for
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage.common.authorisation import jwt_authorization
from frontstage.common.utilities import obfuscate_email
from frontstage.controllers import auth_controller, party_controller
from frontstage.exceptions.exceptions import ApiError, AuthError
from frontstage.models import ChangePasswordFrom, ContactDetailsChangeForm, OptionsForm
from frontstage.views.account import account_bp
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))

BAD_CREDENTIALS_ERROR = "Unauthorized user credentials"
form_redirect_mapper = {
    "contact_details": "account_bp.change_account_details",
    "change_password": "account_bp.change_password",
    "share_surveys": "account_bp.share_survey_overview",
    "transfer_surveys": "account_bp.transfer_surveys",
    "something_else": "account_bp.something_else",
}


@account_bp.route("/", methods=["GET", "POST"])
@jwt_authorization(request)
def account(session):
    page_title = "Account details"
    party_id = session.get_party_id()
    respondent_details = party_controller.get_respondent_party_by_id(party_id)

    if request.method == "POST":
        form = OptionsForm()
        form_valid = form.validate()
        if not form_valid:
            flash("You need to choose an option")
            page_title = "Error: " + page_title
        else:
            return redirect(url_for(form_redirect_mapper.get(form.data["option"])))
    else:
        form = OptionsForm()

    return render_template(
        "account/account.html",
        form=form,
        respondent=respondent_details,
        page_title=page_title,
    )


@account_bp.route("/change-password", methods=["GET", "POST"])
@jwt_authorization(request)
def change_password(session):
    form = ChangePasswordFrom(request.values)
    party_id = session.get_party_id()
    respondent_details = party_controller.get_respondent_party_by_id(party_id)
    if request.method == "POST" and form.validate():
        username = respondent_details["emailAddress"]
        password = request.form.get("password")
        new_password = request.form.get("new_password")
        if new_password == password:
            return render_template(
                "account/account-change-password.html",
                form=form,
                errors={"new_password": ["Your new password is the same as your old password"]},
            )
        bound_logger = logger.bind(email=obfuscate_email(username))
        bound_logger.info("Attempting to find user in auth service")
        try:
            # We call the sign in function to verify that the password provided is correct
            auth_controller.sign_in(username, password)
            bound_logger.info("Attempting to change password via party service")
            party_controller.change_password(username, new_password)
            bound_logger.info("password changed via party service")
            flash("Your password has been changed. Please login with your new password.", "success")
            return redirect(url_for("sign_in_bp.logout"))
        except AuthError as exc:
            error_message = exc.auth_error
            if BAD_CREDENTIALS_ERROR in error_message:
                bound_logger.info("Bad credentials provided")
                return render_template(
                    "account/account-change-password.html",
                    form=form,
                    errors={"password": ["Incorrect current password"]},
                )
    else:
        errors = form.errors

    return render_template("account/account-change-password.html", session=session, form=form, errors=errors)


def change_email_address(session, new_email_address):
    party_id = session.get_party_id()
    respondent_details = party_controller.get_respondent_party_by_id(party_id)
    respondent_details["email_address"] = respondent_details["emailAddress"]
    respondent_details["new_email_address"] = new_email_address
    respondent_details["change_requested_by_respondent"] = True
    logger.info("Attempting to update email address changes on the account", party_id=party_id)
    try:
        party_controller.update_account(respondent_details)

    except ApiError as exc:
        logger.error("Failed to updated email on account", status=exc.status_code, party_id=party_id)
        if exc.status_code == 409:
            logger.info("The email requested already registered in our system. Request denied", party_id=party_id)
            return False
        else:
            raise exc
    logger.info("Successfully updated email on account", party_id=party_id)
    return True


@account_bp.route("/change-account-details", methods=["GET", "POST"])
@jwt_authorization(request)
def change_account_details(session):
    form = ContactDetailsChangeForm(request.values)
    party_id = session.get_party_id()
    respondent_details = party_controller.get_respondent_party_by_id(party_id)
    is_contact_details_update_required = False
    attributes_changed = []
    if request.method == "POST" and form.validate():
        logger.info("Attempting to update contact details changes on the account", party_id=party_id)
        # check_attribute changes also magically updates the respondent_details as a side effect of running this
        # function
        is_contact_details_update_required = check_attribute_change(
            form, attributes_changed, respondent_details, is_contact_details_update_required
        )
        if is_contact_details_update_required:
            try:
                party_controller.update_account(respondent_details)
            except ApiError as exc:
                logger.error("Failed to updated account", status=exc.status_code)
                raise exc
            logger.info("Successfully updated account", party_id=party_id)
        is_email_update_required = form["email_address"].data != respondent_details["emailAddress"]
        if is_email_update_required:
            if not change_email_address(session=session, new_email_address=form["email_address"].data):
                form.errors["email_address"] = ["Email address has already been used to register an account"]
                return render_template(
                    "account/account-contact-detail-change.html",
                    session=session,
                    form=form,
                    errors=form.errors,
                    respondent=respondent_details,
                )
            else:
                flash("We have sent you an email to confirm your new email address.")
        else:
            flash("Your contact details have changed")
        return redirect(url_for("account_bp.account"))
    else:
        return render_template(
            "account/account-contact-detail-change.html",
            session=session,
            form=form,
            errors=form.errors,
            respondent=respondent_details,
        )


def check_attribute_change(form, attributes_changed, respondent_details, update_required_flag):
    """
    Checks if the form data matches with the respondent details

    :param form: the form data
    :param attributes_changed: which attribute changed
    :param respondent_details: respondent data
    :param update_required_flag: boolean flag if update is required
    """
    if form["first_name"].data != respondent_details["firstName"]:
        respondent_details["firstName"] = form["first_name"].data
        update_required_flag = True
        attributes_changed.append("first name")
    if form["last_name"].data != respondent_details["lastName"]:
        respondent_details["lastName"] = form["last_name"].data
        update_required_flag = True
        attributes_changed.append("last name")
    if form["phone_number"].data != respondent_details["telephone"]:
        respondent_details["telephone"] = form["phone_number"].data
        update_required_flag = True
        attributes_changed.append("telephone number")
    return update_required_flag
