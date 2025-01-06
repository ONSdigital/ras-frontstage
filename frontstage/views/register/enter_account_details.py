import logging
from frontstage.common.strtobool import strtobool

from flask import flash, request
from structlog import wrap_logger

from frontstage.common.cryptographer import Cryptographer
from frontstage.common.utilities import obfuscate_email
from frontstage.controllers import iac_controller, party_controller
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import PendingSurveyRegistrationForm, RegistrationForm
from frontstage.views.register import register_bp
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))
cryptographer = Cryptographer()


@register_bp.route("/create-account/enter-account-details", methods=["GET", "POST"])
def register_enter_your_details():
    # Get and decrypt enrolment code
    encrypted_enrolment_code = request.args.get("encrypted_enrolment_code")
    try:
        enrolment_code = cryptographer.decrypt(encrypted_enrolment_code.encode()).decode()
    except AttributeError:
        logger.error("No enrolment code supplied", exc_info=True, url=request.url)
        raise
    form = RegistrationForm(request.values, enrolment_code=encrypted_enrolment_code)
    if form.email_address.data is not None:
        form.email_address.data = form.email_address.data.strip()

    # Validate enrolment code before rendering or checking the form
    iac_controller.validate_enrolment_code(enrolment_code)

    if request.method == "POST" and form.validate():
        email_address = form.email_address.data

        registration_data = {
            "emailAddress": email_address,
            "firstName": request.form.get("first_name"),
            "lastName": request.form.get("last_name"),
            "password": request.form.get("password"),
            "telephone": request.form.get("phone_number"),
            "enrolmentCode": enrolment_code,
        }

        try:
            party_controller.create_account(registration_data)
        except ApiError as exc:
            if exc.status_code == 400:
                # If party returns an error, we should just log out the error with as much detail as possible, and
                # put a generic message up for the user as we don't want to show them any potentially ugly messages
                # from party
                logger.info(
                    "Party returned an error",
                    email=obfuscate_email(email_address),
                    enrolment_code=enrolment_code,
                    error=exc.message,
                )
                flash("Something went wrong, please try again or contact us", "error")
                return render_template("register/enter-your-details.html", form=form, errors=form.errors)
            elif exc.status_code == 409:
                error = {"email_address": ["This email has already been used to register an account"]}
                return render_template("register/enter-your-details.html", form=form, errors=error)
            else:
                logger.error("Failed to create account", status=exc.status_code, error=exc.message)
                raise exc

        return render_template("register/almost-done.html", email=email_address)

    else:
        return render_template("register/enter-your-details.html", form=form, errors=form.errors)


@register_bp.route("/pending-surveys/create-account/enter-account-details", methods=["GET", "POST"])
def pending_surveys_register_enter_your_details():
    """
     Registration endpoint for account creation and
     verification against share surveys  and transfer surveys (Account does not exist)
    :return:
    :rtype:
    """
    # Get and decrypt enrolment code
    batch_no = request.args.get("batch_no", None)
    email = request.args.get("email", None)
    is_transfer = request.args.get("is_transfer", None)
    form = PendingSurveyRegistrationForm(request.values, batch_no=batch_no, email=email, is_transfer=is_transfer)
    # Validate batch_no before rendering or checking the form
    party_controller.get_pending_surveys_batch_number(batch_no)
    if request.method == "POST" and form.validate():
        logger.info("Attempting to create account against share/transfer surveys email address")
        email_address = form.email.data
        registration_data = {
            "emailAddress": email_address,
            "firstName": request.form.get("first_name"),
            "lastName": request.form.get("last_name"),
            "password": request.form.get("password"),
            "telephone": request.form.get("phone_number"),
            "batch_no": batch_no,
        }

        try:
            logger.info("Calling party service to create account against share/transfer surveys email address")
            party_controller.create_pending_survey_account(registration_data)
        except ApiError as exc:
            if exc.status_code == 400:
                logger.info("pending surveys email address already in use")
                error = {"email_address": ["This email has already been used to register an account"]}
                return render_template(
                    "register/register-pending-survey-enter-your-details.html", form=form, errors=error, email=email
                )
            else:
                logger.error(
                    "Failed to create/register new account  against pending surveys email address",
                    status=exc.status_code,
                )
                raise exc

        logger.info("Successfully created/registered new account against pending surveys email address")
        return render_template(
            "register/register-pending-survey-registration-complete.html", is_transfer=bool(strtobool(is_transfer))
        )

    else:
        return render_template(
            "register/register-pending-survey-enter-your-details.html", form=form, errors=form.errors, email=email
        )
