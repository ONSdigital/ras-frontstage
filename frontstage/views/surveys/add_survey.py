import logging
from os import getenv

from flask import redirect, request, url_for
from structlog import wrap_logger

from frontstage.common.authorisation import jwt_authorization
from frontstage.common.cryptographer import Cryptographer
from frontstage.controllers import iac_controller
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import EnrolmentCodeForm
from frontstage.views.surveys import surveys_bp
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))

ERROR_MESSAGE = "Enter a valid enrolment code"


@surveys_bp.route("/add-survey", methods=["GET", "POST"])
@jwt_authorization(request)
def add_survey(session):
    form = EnrolmentCodeForm(request.form)
    error_message = ""
    if request.method == "POST":
        enrolment_code = request.form.get("enrolment_code").lower()
        logger.info("Enrolment code submitted when attempting to add survey", enrolment_code=enrolment_code)
        if not form.validate():
            error_message = ERROR_MESSAGE
        else:
            # Validate the enrolment code
            try:
                iac = iac_controller.get_iac_from_enrolment(enrolment_code)
                if iac is None or not iac["active"]:
                    error_message = ERROR_MESSAGE
            except ApiError:
                error_message = ERROR_MESSAGE
        if not error_message:
            cryptographer = Cryptographer()
            encrypted_enrolment_code = cryptographer.encrypt(enrolment_code.encode()).decode()
            return redirect(
                url_for(
                    "surveys_bp.survey_confirm_organisation",
                    encrypted_enrolment_code=encrypted_enrolment_code,
                    _external=True,
                    _scheme=getenv("SCHEME", "http"),
                )
            )
    return render_template("surveys/surveys-add.html", session=session, form=form, error=error_message)
