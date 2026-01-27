import logging

from flask import abort, request
from structlog import wrap_logger

from frontstage import app
from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import (
    case_controller,
    collection_instrument_controller,
    party_controller,
    survey_controller,
)
from frontstage.exceptions.exceptions import CiUploadError, NoSurveyPermission
from frontstage.views.surveys import surveys_bp
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))

SINGLE_VALIDATION_ERROR = "There is 1 error on this page"


@surveys_bp.route("/upload-survey", methods=["POST"])
@jwt_authorization(request)
def upload_survey(session):
    party_id = session.get_party_id()
    case_id = request.args["case_id"]
    business_party_id = request.args["business_party_id"]
    survey_short_name = request.args["survey_short_name"]

    logger.info("Attempting to upload collection instrument", case_id=case_id, party_id=party_id)

    if not (case_id or business_party_id or survey_short_name):
        logger.error(
            "upload_survey did not include case_id, business_party_id or survey_short_name",
            case_id=case_id,
            party_id=party_id,
        )
        abort(400)

    # Check if respondent has permission to upload for this case
    survey = survey_controller.get_survey_by_short_name(survey_short_name)
    if not party_controller.is_respondent_enrolled(party_id, business_party_id, survey["id"]):
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

    upload_file = request.files["file"]
    content_length = request.content_length

    try:
        validation_errors = collection_instrument_controller.upload_collection_instrument(
            upload_file, content_length, case, business_party, party_id, survey
        )
        if validation_errors is not None:
            error_title = (
                SINGLE_VALIDATION_ERROR
                if len(validation_errors) == 1
                else f"There are {len(validation_errors)} errors on this page"
            )
            return render_template(
                "surveys/surveys-upload-failure.html",
                session=session,
                business_info=business_party,
                survey_info=survey,
                errors=validation_errors,
                case_id=case_id,
                error_title=error_title,
            )

    except CiUploadError as ex:
        upload_error = determine_error_type(ex)
        if not upload_error:
            logger.error(
                "Unexpected error message returned from collection instrument service",
                error_message=ex.error_message,
                party_id=party_id,
                case_id=case_id,
            )
            upload_error = "unexpected"
        return render_template(
            "surveys/surveys-upload-failure.html",
            session=session,
            business_info=business_party,
            survey_info=survey,
            errors=[upload_error],
            case_id=case_id,
            error_title=SINGLE_VALIDATION_ERROR,
        )

    logger.info("Successfully uploaded collection instrument", party_id=party_id, case_id=case_id)
    return render_template(
        "surveys/surveys-upload-success.html",
        session=session,
        upload_filename=upload_file.filename,
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
