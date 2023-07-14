import logging

from flask import request
from structlog import wrap_logger

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import case_controller, conversation_controller
from frontstage.views.surveys import surveys_bp
from frontstage.views.template_helper import render_template

logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route("/upload-failed", methods=["GET"])
@jwt_authorization(request)
def upload_failed(session):
    case_id = request.args.get("case_id")
    business_party_id = request.args["business_party_id"]
    survey_short_name = request.args["survey_short_name"]
    party_id = session.get_party_id()
    error_info = request.args.get("error_info", None)

    case_data = case_controller.get_case_data(case_id, party_id, business_party_id, survey_short_name)

    # Select correct error text depending on error_info
    if error_info == "type":
        error_info = {
            "header": "Error uploading - incorrect file type",
            "body": "The spreadsheet must be in .xls or .xlsx format",
        }
    elif error_info == "charLimit":
        error_info = {
            "header": "Error uploading - file name too long",
            "body": "The file name of your spreadsheet must be " "less than 50 characters long",
        }
    elif error_info == "size":
        error_info = {
            "header": "Error uploading - file size too large",
            "body": "The spreadsheet must be smaller than 20MB in size",
        }
    elif error_info == "sizeSmall":
        error_info = {
            "header": "Error uploading - file size too small",
            "body": "The spreadsheet must be larger than 6KB in size",
        }
    else:
        error_info = {"header": "Something went wrong", "body": "Please try uploading your spreadsheet again"}
    unread_message_count = {"unread_message_count": conversation_controller.try_message_count_from_session(session)}
    return render_template(
        "surveys/surveys-upload-failure.html",
        session=session,
        business_info=case_data["business_party"],
        survey_info=case_data["survey"],
        collection_exercise_info=case_data["collection_exercise"],
        error_info=error_info,
        case_id=case_id,
        unread_message_count=unread_message_count,
    )
