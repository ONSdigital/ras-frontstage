import logging
from datetime import datetime

from flask import make_response, request
from flask import session as flask_session
from structlog import wrap_logger

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import conversation_controller, party_controller
from frontstage.views.surveys import surveys_bp
from frontstage.views.template_helper import render_template

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
    survey_shared = request.args.get("survey_shared")
    transfer_dict = None

    logger.info(
        "Retrieving survey list",
        party_id=party_id,
        business_id=business_id,
        survey_id=survey_id,
        already_enrolled=already_enrolled,
        tag=tag,
    )

    respondent_enrolments = party_controller.get_respondent_enrolments(party_id)
    survey_list = party_controller.get_survey_list_details_for_party(
        respondent_enrolments, tag, business_party_id=business_id, survey_id=survey_id
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

    unread_message_count = {"unread_message_count": conversation_controller.try_message_count_from_session(session)}
    if tag == "todo":
        added_survey = True if business_id and survey_id and not already_enrolled else None
        if flask_session.get("transferred_surveys"):
            transfer_dict = flask_session.get("transferred_surveys")
            flask_session.pop("transferred_surveys")
        response = make_response(
            render_template(
                "surveys/surveys-todo.html",
                session=session,
                sorted_surveys_list=sorted_survey_list,
                added_survey=added_survey,
                already_enrolled=already_enrolled,
                unread_message_count=unread_message_count,
                delete_option_allowed=True if len(respondent_enrolments) == 0 else False,
                survey_shared=survey_shared,
                transfer_dict=transfer_dict,
            )
        )

        # Ensure any return to list of surveys (e.g. browser back) round trips the server to display the latest statuses
        response.headers.set("Cache-Control", "no-cache, max-age=0, must-revalidate, no-store")

        return response
    else:
        return render_template(
            "surveys/surveys-history.html",
            session=session,
            sorted_surveys_list=sorted_survey_list,
            history=True,
            unread_message_count=unread_message_count,
        )
