import logging
from datetime import datetime

from flask import render_template, request, make_response
from structlog import wrap_logger

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import party_controller
from frontstage.views.surveys import surveys_bp


logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route('/<tag>', methods=['GET'])
@jwt_authorization(request)
def get_survey_list(session, tag):
    logger.info("Retrieving survey todo list")
    party_id = session.get('party_id')
    business_id = request.args.get('business_party_id')
    survey_id = request.args.get('survey_id')
    already_enrolled = request.args.get('already_enrolled')

    survey_list = party_controller.get_survey_list_details_for_party(party_id, tag, business_party_id=business_id,
                                                                     survey_id=survey_id)

    sorted_survey_list = sorted(survey_list, key=lambda k: datetime.strptime(k['submit_by'], '%d %b %Y'))

    if tag == 'todo':
        response = make_response(render_template('surveys/surveys-todo.html',
                                                 sorted_surveys_list=sorted_survey_list,
                                                 added_survey=True if business_id and survey_id and not already_enrolled else None,
                                                 already_enrolled=already_enrolled
                                                 ))

        # Ensure any return to list of surveys (e.g. browser back) round trips the server to display the latest statuses
        response.headers.set("Cache-Control", "no-cache, max-age=0, must-revalidate, no-store")

        return response
    else:
        return render_template('surveys/surveys-history.html', sorted_surveys_list=sorted_survey_list, history=True)
