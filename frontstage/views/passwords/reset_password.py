import logging

from flask import abort
from flask import current_app as app
from flask import flash, redirect, request, url_for
from itsdangerous import BadData, BadSignature, SignatureExpired
from structlog import wrap_logger
from werkzeug.exceptions import NotFound

from frontstage.common import verification
from frontstage.controllers import party_controller
from frontstage.controllers.notify_controller import NotifyGateway
from frontstage.exceptions.exceptions import ApiError, RasNotifyError
from frontstage.models import ResetPasswordForm
from frontstage.views.passwords import passwords_bp
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))


@passwords_bp.route("/reset-password/<token>", methods=["GET"])
def get_reset_password(token, form_errors=None):
    form = ResetPasswordForm(request.form)

    try:
        duration = app.config["EMAIL_TOKEN_EXPIRY"]
        email = verification.decode_email_token(token, duration)
        respondent = party_controller.get_respondent_by_email(email)
        db_token = respondent["password_verification_token"]
        if not token == db_token:
            logger.warning("Token not found for respondent", token=token, respondent_id=respondent["id"])
            return render_template("passwords/password-token-not-found.html", token=token)
    except KeyError:
        logger.warning("Token not found for respondent", token=token, exc_info=True)
        return render_template("passwords/password-token-not-found.html", token=token)
    except SignatureExpired:
        try:
            party_controller.delete_verification_token(token)
        except NotFound:
            return render_template("passwords/password-token-not-found.html", token=token)
        logger.warning("Token expired for frontstage reset", token=token, exc_info=True)
        return render_template("passwords/password-expired.html", token=token)
    except (BadSignature, BadData):
        logger.warning("Invalid token sent to frontstage password reset", token=token, exc_info=True)
        return render_template("passwords/password-expired.html", token=token)
    except TypeError:
        logger.error("Type error when decoding and using token", token=token, exc_info=True)
        return render_template("passwords/password-token-not-found.html", token=token)

    template_data = {"error": {"type": form_errors}, "token": token}
    return render_template("passwords/reset-password.html", form=form, data=template_data)


@passwords_bp.route("/reset-password/<token>", methods=["POST"])
def post_reset_password(token):
    form = ResetPasswordForm(request.form)

    if not form.validate():
        return get_reset_password(token, form_errors=form.errors)

    password = request.form.get("password")

    try:
        duration = app.config["EMAIL_TOKEN_EXPIRY"]
        email = verification.decode_email_token(token, duration)
        party_controller.change_password(email, password)
        party_controller.delete_verification_token(token)
    except ApiError as exc:
        if exc.status_code == 409:
            logger.warning("Token expired", api_url=exc.url, api_status_code=exc.status_code, token=token)
            return render_template("passwords/password-expired.html", token=token)
        elif exc.status_code == 404:
            logger.warning(
                "Invalid token sent to party service", api_url=exc.url, api_status_code=exc.status_code, token=token
            )
            abort(404)
        else:
            raise exc

    logger.info("Successfully changed user password", token=token)
    return redirect(url_for("passwords_bp.reset_password_confirmation"))


@passwords_bp.route("/reset-password/confirmation", methods=["GET"])
def reset_password_confirmation():
    return render_template("passwords/reset-password.confirmation.html")


@passwords_bp.route("/reset-password/check-email/<token>", methods=["GET"])
def reset_password_check_email(token):
    email = verification.decode_email_token(token)
    return render_template("passwords/reset-password.check-email.html", email=email)


@passwords_bp.route("/reset-password/exceeded-attempts", methods=["GET"])
def exceeded_number_of_reset_attempts():
    return render_template("passwords/exceeded-password-reset-attempts.html")


@passwords_bp.route("/reset-password-trouble", methods=["GET"])
def reset_password_trouble():
    return render_template("passwords/reset-password-trouble.html")


@passwords_bp.route("/resend-password-email-expired-token/<token>", methods=["GET"])
def resend_password_email_expired_token(token):
    email = verification.decode_email_token(token)
    party_controller.post_verification_token(email, token)
    return request_password_change(email)


def request_password_change(email):
    respondent = party_controller.get_respondent_by_email(email)

    if not respondent:
        logger.info("Respondent does not exist")
        return redirect(url_for("passwords_bp.reset_password_trouble"))

    party_id = str(respondent["id"])
    password_reset_counter = party_controller.get_password_reset_counter(party_id)["counter"]

    if password_reset_counter >= 5:
        verification_token = respondent.get("password_verification_token")
        try:
            verification.decode_email_token(verification_token, app.config["PASSWORD_RESET_ATTEMPTS_TIMEOUT"])
            logger.error("Password reset attempts exceeded")
            return redirect(url_for("passwords_bp.exceeded_number_of_reset_attempts"))
        except (BadSignature, SignatureExpired):
            try:
                party_controller.reset_password_reset_counter(party_id)
            except ApiError:
                logger.error("Error resetting password reset counter")
                return redirect(url_for("passwords_bp.reset_password_trouble"))

    # When the password_verification_token has expired, it will be deleted from the DB
    if verification_token := respondent.get("password_verification_token"):
        try:
            email = verification.decode_email_token(verification_token, app.config["PASSWORD_RESET_ATTEMPTS_TIMEOUT"])
        except SignatureExpired:
            try:
                party_controller.reset_password_reset_counter(party_id)
            except ApiError:
                logger.error("Error resetting password reset counter")
                return redirect(url_for("passwords_bp.reset_password_trouble"))

    logger.info("Requesting password change", party_id=party_id)

    token = verification.generate_email_token(email)

    url_root = request.url_root
    # url_for comes with a leading slash, so strip off the trailing slash in url_root if there is one
    if url_root.endswith("/"):
        url_root = url_root[:-1]
    verification_url = url_root + url_for("passwords_bp.post_reset_password", token=token)

    personalisation = {"RESET_PASSWORD_URL": verification_url, "FIRST_NAME": respondent["firstName"]}

    logger.info("Reset password url", url=verification_url, party_id=party_id)

    party_controller.post_verification_token(email, token)

    try:
        NotifyGateway(app.config).request_to_notify(email=email, personalisation=personalisation, reference=party_id)
        logger.info("Password reset email successfully sent", party_id=party_id)
    except RasNotifyError:
        # Note: intentionally suppresses exception
        logger.error("Error sending request to Notify Gateway", respondent_id=party_id, exc_info=True)

    # Get real time counter to check how many attempts are left
    password_reset_counter = party_controller.get_password_reset_counter(party_id)["counter"]
    if password_reset_counter == 4:
        flash(message="You have 1 try left to reset your password", category="warn")

    return redirect(url_for("passwords_bp.reset_password_check_email", token=token))
