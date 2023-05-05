import logging
from datetime import datetime, timezone

from flask import make_response, render_template, request
from flask import session as flask_session
from structlog import wrap_logger

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import conversation_controller, party_controller
from frontstage.views.surveys import surveys_bp

logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route("/<tag>", methods=["GET"])
@jwt_authorization(request)
def get_survey_list(session, tag):
    """
    Displays the list of surveys for the respondent by tag.  A tag represents the state the
    survey is in (e.g., todo, history, etc)
    """
    flask_session.pop("help_survey_ref", None)
    flask_session.pop("help_ru_ref", None)
    party_id = session.get_party_id()
    business_id = request.args.get("business_party_id")
    survey_id = request.args.get("survey_id")
    already_enrolled = request.args.get("already_enrolled")
    logger.info(
        "Retrieving survey list",
        party_id=party_id,
        business_id=business_id,
        survey_id=survey_id,
        already_enrolled=already_enrolled,
        tag=tag,
    )

    # This logic is added to make sure a user is provided an option to delete an account if there is no
    # active enrolment which is ENABLED
    respondent = party_controller.get_respondent_party_by_id(party_id)
    delete_option_allowed = is_delete_account_respondent_allowed(respondent)

    survey_list = party_controller.get_survey_list_details_for_party(
        respondent, tag, business_party_id=business_id, survey_id=survey_id
    )
    sorted_survey_list = sorted(survey_list, key=lambda k: datetime.strptime(k["submit_by"], "%d %b %Y"), reverse=True)
    logger.info(
        "Successfully retrieved survey list",
        party_id=party_id,
        business_id=business_id,
        survey_id=survey_id,
        already_enrolled=already_enrolled,
        tag=tag,
    )

    expires_at = session.get_formatted_expires_in()

    unread_message_count = {"unread_message_count": conversation_controller.try_message_count_from_session(session)}
    if tag == "todo":
        added_survey = True if business_id and survey_id and not already_enrolled else None
        response = make_response(
            render_template(
                "surveys/surveys-todo.html",
                sorted_surveys_list=sorted_survey_list,
                added_survey=added_survey,
                already_enrolled=already_enrolled,
                unread_message_count=unread_message_count,
                delete_option_allowed=delete_option_allowed,
                expires_at=expires_at,
            )
        )

        # Ensure any return to list of surveys (e.g. browser back) round trips the server to display the latest statuses
        response.headers.set("Cache-Control", "no-cache, max-age=0, must-revalidate, no-store")

        return response
    else:
        return render_template(
            "surveys/surveys-history.html",
            sorted_surveys_list=sorted_survey_list,
            history=True,
            unread_message_count=unread_message_count,
            expires_at=expires_at,
        )


def is_delete_account_respondent_allowed(respondent: dict) -> bool:
    """
    Determine if the user has any active enrolments for the purpose of displaying the delete account option

    :param respondent: A dict containing respondent data
    :return: True if allowed, false if not.
    """
    if "associations" in respondent:
        for association in respondent["associations"]:
            for enrolment in association["enrolments"]:
                if enrolment["enrolmentStatus"] == "ENABLED":
                    return False
    return True
