import logging

from flask import abort, redirect, request, url_for
from itsdangerous import BadSignature, URLSafeSerializer
from structlog import wrap_logger

from frontstage import app
from frontstage.models import ForgotPasswordForm
from frontstage.views.passwords import passwords_bp, reset_password
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))


BAD_AUTH_ERROR = "Unauthorized user credentials"

url_safe_serializer = URLSafeSerializer(app.config["SECRET_KEY"])


@passwords_bp.route("/forgot-password", methods=["GET"])
def get_forgot_password():
    form = ForgotPasswordForm(request.form)
    return render_template("passwords/forgot-password.html", form=form)


@passwords_bp.route("/forgot-password", methods=["POST"])
def post_forgot_password():
    form = ForgotPasswordForm(request.form)
    email = form.data.get("email_address").strip()

    if form.validate():
        return reset_password.request_password_change(email)

    return render_template("passwords/forgot-password.html", form=form, email=email)


@passwords_bp.route("/forgot-password/check-email", methods=["GET"])
def forgot_password_check_email():
    encoded_email = request.args.get("email", None)

    if encoded_email is None:
        logger.error("No email parameter supplied")
        return redirect(url_for("passwords_bp.get_forgot_password"))

    try:
        email = url_safe_serializer.loads(encoded_email)
    except BadSignature:
        logger.error("Unable to decode email from URL", encoded_email=encoded_email)
        abort(404)

    return render_template("passwords/forgot-password.check-email.html", email=email)
