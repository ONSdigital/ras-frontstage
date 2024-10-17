import logging
from os import getenv

from flask import make_response, redirect, request, session, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.session import Session
from frontstage.common.utilities import obfuscate_email
from frontstage.controllers import (
    auth_controller,
    conversation_controller,
    party_controller,
)
from frontstage.controllers.party_controller import (
    notify_party_and_respondent_account_locked,
)
from frontstage.exceptions.exceptions import AuthError
from frontstage.models import LoginForm
from frontstage.views.sign_in import sign_in_bp
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))

UNKNOWN_ACCOUNT_ERROR = "Authentication error in Auth service"
BAD_AUTH_ERROR = "Unauthorized user credentials"
NOT_VERIFIED_ERROR = "User account not verified"
USER_ACCOUNT_LOCKED = "User account locked"
USER_ACCOUNT_DELETED = "User account deleted"


@app.route("/", methods=["GET"])
def home():
    return redirect(url_for("sign_in_bp.login", _external=True, _scheme=getenv("SCHEME", "http")))


@sign_in_bp.route("/", methods=["GET", "POST"])
def login():  # noqa: C901
    form = LoginForm(request.form)

    if form.username.data is not None:
        form.username.data = form.username.data.strip()

    if request.method == "POST" and form.validate():
        username = form.username.data
        password = request.form.get("password")
        bound_logger = logger.bind(email=obfuscate_email(username))
        bound_logger.info("Attempting to find user in auth service")
        try:
            auth_controller.sign_in(username, password)
        except AuthError as exc:
            error_message = exc.auth_error
            party_json = party_controller.get_respondent_by_email(username)
            party_id = party_json.get("id") if party_json else None
            bound_logger = bound_logger.bind(party_id=party_id)

            if USER_ACCOUNT_LOCKED in error_message:
                if not party_id:
                    bound_logger.error("Respondent account locked in auth but doesn't exist in party")
                    return render_template("sign-in/sign-in.html", form=form, data={"error": {"type": "failed"}})
                bound_logger.info("User account is locked on the Auth server", status=party_json["status"])
                if party_json["status"] == "ACTIVE" or party_json["status"] == "CREATED":
                    notify_party_and_respondent_account_locked(
                        respondent_id=party_id, email_address=username, status="SUSPENDED"
                    )
                return render_template("sign-in/sign-in.account-locked.html", form=form)
            elif NOT_VERIFIED_ERROR in error_message:
                bound_logger.info("User account is not verified on the Auth server")
                return render_template("sign-in/sign-in.account-not-verified.html", party_id=party_id)
            elif BAD_AUTH_ERROR in error_message:
                bound_logger.info("Bad credentials provided")
            elif UNKNOWN_ACCOUNT_ERROR in error_message:
                bound_logger.info("User account does not exist in auth service")
            elif USER_ACCOUNT_DELETED in error_message:
                bound_logger.info("User account is marked for deletion")
            else:
                bound_logger.error("Unexpected error was returned from Auth service", auth_error=error_message)

            bound_logger.unbind("email")
            return render_template(
                "sign-in/sign-in.html",
                form=form,
                data={"error": {"type": "failed"}},
            )

        bound_logger.info("Successfully found user in auth service.  Attempting to find user in party service")
        party_json = party_controller.get_respondent_by_email(username)
        if not party_json or "id" not in party_json:
            bound_logger.error("Respondent has an account in auth but not in party")
            return render_template(
                "sign-in/sign-in.html",
                form=form,
                data={"error": {"type": "failed"}},
            )
        party_id = party_json["id"]
        bound_logger = bound_logger.bind(party_id=party_id)

        if session.get("next"):
            response = make_response(redirect(session.get("next")))
            session.pop("next")
        else:
            response = make_response(
                redirect(
                    url_for("surveys_bp.get_survey_list", tag="todo", _external=True, _scheme=getenv("SCHEME", "http"))
                )
            )

        bound_logger.info("Successfully found user in party service")
        bound_logger.info("Creating session")
        redis_session = Session.from_party_id(party_id)
        response.set_cookie(
            "authorization",
            value=redis_session.session_key,
            secure=app.config["SECURE_APP"],
            httponly=True,
            samesite="strict",
        )
        count = conversation_controller.get_message_count_from_api(redis_session)
        redis_session.set_unread_message_total(count)
        bound_logger.info("Successfully created session", session_key=redis_session.session_key)
        bound_logger.unbind("email")
        return response

    account_activated = request.args.get("account_activated", None)
    template_data = {"error": {"type": form.errors, "logged_in": "False"}, "account_activated": account_activated}
    return render_template("sign-in/sign-in.html", form=form, data=template_data)


@sign_in_bp.route("/resend_verification/<party_id>", methods=["GET"])  # Deprecated: to be removed when not in use
@sign_in_bp.route("/resend-verification/<party_id>", methods=["GET"])
def resend_verification(party_id):
    party_controller.resend_verification_email(party_id)
    logger.info("Re-sent verification email.", party_id=party_id)
    return render_template("sign-in/sign-in.verification-email-sent.html")


@sign_in_bp.route("/resend-verification-expired-token/<token>", methods=["GET"])
def resend_verification_expired_token(token):
    party_controller.resend_verification_email_expired_token(token)
    logger.info("Re-sent verification email for expired token.", token=token)
    return render_template("sign-in/sign-in.verification-email-sent.html")
