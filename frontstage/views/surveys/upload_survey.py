import logging

from flask import redirect, render_template, request, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import (
    case_controller,
    collection_instrument_controller,
    conversation_controller,
    party_controller,
    survey_controller,
)
from frontstage.exceptions.exceptions import CiUploadError, NoSurveyPermission
from frontstage.views.surveys import surveys_bp

logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route("/upload-survey", methods=["POST"])
@jwt_authorization(request)
def upload_survey(session):
    party_id = session.get_party_id()
    case_id = request.args["case_id"]
    business_party_id = request.args["business_party_id"]
    survey_short_name = request.args["survey_short_name"]
    logger.info("Attempting to upload collection instrument", case_id=case_id, party_id=party_id)

    if request.content_length > app.config["MAX_UPLOAD_LENGTH"]:
        return redirect(
            url_for(
                "surveys_bp.upload_failed",
                _external=True,
                case_id=case_id,
                business_party_id=business_party_id,
                survey_short_name=survey_short_name,
                error_info="size",
            )
        )

    # Check if respondent has permission to upload for this case
    survey = survey_controller.get_survey_by_short_name(survey_short_name)
    if not party_controller.is_respondent_enrolled(party_id, business_party_id, survey):
        raise NoSurveyPermission(party_id, case_id)

    case = case_controller.get_case_by_case_id(case_id)

    case_group = case.get("caseGroup")
    collection_exercise_id = case_group.get("collectionExerciseId")
    business_party = party_controller.get_party_by_business_id(
        case_group["partyId"],
        app.config["PARTY_URL"],
        app.config["BASIC_AUTH"],
        collection_exercise_id=collection_exercise_id,
        verbose=True,
    )

    # Get the uploaded file
    upload_file = request.files["file"]

    try:
        # Upload the file to the collection instrument service
        collection_instrument_controller.upload_collection_instrument(
            upload_file, case, business_party, party_id, survey
        )
    except CiUploadError as ex:
        error_type = determine_error_type(ex)
        if not error_type:
            logger.error(
                "Unexpected error message returned from collection instrument service",
                error_message=ex.error_message,
                party_id=party_id,
                case_id=case_id,
            )
            error_type = "unexpected"
        return redirect(
            url_for(
                "surveys_bp.upload_failed",
                _external=True,
                case_id=case_id,
                business_party_id=business_party_id,
                survey_short_name=survey_short_name,
                error_info=error_type,
            )
        )

    logger.info("Successfully uploaded collection instrument", party_id=party_id, case_id=case_id)
    unread_message_count = {"unread_message_count": conversation_controller.try_message_count_from_session(session)}
    return render_template(
        "surveys/surveys-upload-success.html",
        upload_filename=upload_file.filename,
        unread_message_count=unread_message_count,
    )


def determine_error_type(ex):
    error_type = ""
    if ".xlsx format" in ex.error_message:
        error_type = "type"
    elif "50 characters" in ex.error_message:
        error_type = "charLimit"
    elif "File too large" in ex.error_message:
        error_type = "size"
    elif "File too small" in ex.error_message:
        error_type = "sizeSmall"
    return error_type
