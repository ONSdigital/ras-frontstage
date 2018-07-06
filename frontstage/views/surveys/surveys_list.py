import logging

from flask import render_template, request, make_response
from structlog import wrap_logger

from frontstage.controllers import party_controller
from frontstage.common.authorisation import jwt_authorization
from frontstage.views.surveys import surveys_bp


logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route('/<tag>', methods=['GET'])
@jwt_authorization(request)
def get_survey_list(session, tag):
    logger.info("Retrieving survey todo list")
    party_id = session.get('party_id')

    survey_list = party_controller.get_party_enabled_enrolments_details(party_id, tag)

    sorted_survey_list = sorted(survey_list, key=lambda k: k['return_by'], reverse=True)

    if tag == 'todo':
        response = make_response(render_template('surveys/surveys-todo.html',
                                                 just_added_case_id=request.args.get('case_id'),
                                                 sorted_surveys_list=sorted_survey_list))

        # Ensure any return to list of surveys (e.g. browser back) round trips the server to display the latest statuses
        response.headers.set("Cache-Control", "no-cache, max-age=0, must-revalidate, no-store")

        return response
    else:
        return render_template('surveys/surveys-todo.html', sorted_surveys_list=sorted_survey_list, history=True)
