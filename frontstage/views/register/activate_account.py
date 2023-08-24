import logging
from os import getenv

from flask import abort, redirect, url_for
from structlog import wrap_logger

from frontstage.controllers import party_controller
from frontstage.exceptions.exceptions import ApiError
from frontstage.views.register import register_bp
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))


@register_bp.route("/activate-account/<token>", methods=["GET"])
def register_activate_account(token):
    logger.info("Attempting to verify email", token=token)

    try:
        party_controller.verify_email(token)
    except ApiError as exc:
        # Handle api errors
        if exc.status_code == 409:
            logger.info(
                "Expired email verification token", token=token, api_url=exc.url, api_status_code=exc.status_code
            )
            return render_template("register/link-expired.html", token=token)
        elif exc.status_code == 404:
            logger.warning(
                "Unrecognised email verification token", token=token, api_url=exc.url, api_status_code=exc.status_code
            )
            abort(404)
        else:
            logger.info("Failed to verify email", token=token, api_url=exc.url, api_status_code=exc.status_code)
            raise exc

    # Successful account activation therefore redirect back to the login screen
    logger.info("Successfully verified email", token=token)
    return redirect(
        url_for("sign_in_bp.login", account_activated=True, _external=True, _scheme=getenv("SCHEME", "http"))
    )
