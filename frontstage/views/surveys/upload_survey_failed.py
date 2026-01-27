import logging

from flask import request
from structlog import wrap_logger

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import case_controller
from frontstage.views.surveys import surveys_bp
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route("/upload_failed", methods=["GET"])
@jwt_authorization(request)
def upload_failed(session):
    case_id = request.args.get("case_id")
    business_party_id = request.args["business_party_id"]
    survey_short_name = request.args["survey_short_name"]
    party_id = session.get_party_id()
    error_info = request.args.get("error_info", None)

    case_data = case_controller.get_case_data(case_id, party_id, business_party_id, survey_short_name)

    # Select correct error text depending on error_info

    print(error_info)

    return render_template(
        "surveys/surveys-upload-failure.html",
        session=session,
        business_info=case_data["business_party"],
        survey_info=case_data["survey"],
        collection_exercise_info=case_data["collection_exercise"],
        error_info=error_info,
        case_id=case_id,
    )
