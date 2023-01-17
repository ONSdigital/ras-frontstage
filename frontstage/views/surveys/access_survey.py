import logging

from flask import redirect, render_template, request
from structlog import wrap_logger

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import (
    case_controller,
    collection_exercise_controller,
    conversation_controller,
)
from frontstage.views.surveys import surveys_bp

logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route("/access-survey", methods=["GET"])
@jwt_authorization(request)
def access_survey(session):
    party_id = session.get_party_id()
    case_id = request.args["case_id"]
    business_party_id = request.args["business_party_id"]
    survey_short_name = request.args["survey_short_name"]
    collection_instrument_type = request.args["ci_type"]

    if collection_instrument_type == "EQ":
        logger.info("Attempting to redirect to EQ", party_id=party_id, case_id=case_id)
        case = case_controller.get_case_by_case_id(case_id)
        collection_exercise = collection_exercise_controller.get_collection_exercise(
            case["caseGroup"]["collectionExerciseId"]
        )
        return redirect(
            case_controller.get_eq_url(case, collection_exercise, party_id, business_party_id, survey_short_name)
        )

    logger.info("Retrieving case data", party_id=party_id, case_id=case_id)
    case_data = case_controller.get_case_data(case_id, party_id, business_party_id, survey_short_name)
    referer_header = request.headers.get("referer", {})

    logger.info("Successfully retrieved case data", party_id=party_id, case_id=case_id)
    unread_message_count = {"unread_message_count": conversation_controller.try_message_count_from_session(session)}
    return render_template(
        "surveys/surveys-access.html",
        case_id=case_id,
        collection_instrument_id=case_data["collection_instrument"]["id"],
        collection_instrument_size=case_data["collection_instrument"]["len"],
        survey_info=case_data["survey"],
        collection_exercise_info=case_data["collection_exercise"],
        business_info=case_data["business_party"],
        referer_header=referer_header,
        unread_message_count=unread_message_count,
    )
