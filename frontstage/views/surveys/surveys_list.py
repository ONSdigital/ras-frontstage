import logging

from flask import render_template, request, make_response
from structlog import wrap_logger

from frontstage.controllers import case_controller, party_controller, survey_controller
from frontstage.common.authorisation import jwt_authorization
from frontstage.views.surveys import surveys_bp


logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route('/todo', methods=['GET'])
@jwt_authorization(request)
def logged_in(session):
    party_id = session.get('party_id')

    cases = case_controller.get_cases_by_party_id(party_id, case_events=True)
    surveys_list = survey_controller.get_surveys_list(cases, party_id, 'todo')
    sorted_surveys_list = sorted(surveys_list, key=lambda k: k['collection_exercise']['scheduledReturnDateTime'],
                                 reverse=True)

    response = make_response(render_template('surveys/surveys-todo.html',
                             just_added_case_id=request.args.get('case_id'),
                             sorted_surveys_list=sorted_surveys_list))

    # Ensure any return to list of surveys (e.g. browser back) round trips the server to display the latest statuses
    response.headers.set("Cache-Control", "no-cache, max-age=0, must-revalidate, no-store")

    return response


@surveys_bp.route('/history', methods=['GET'])
@jwt_authorization(request)
def surveys_history(session):
    party_id = session['party_id']
    cases = case_controller.get_cases_by_party_id(party_id, case_events=True)
    sorted_surveys_list = survey_controller.get_surveys_list(cases, party_id, 'history')
    return render_template('surveys/surveys-history.html', sorted_surveys_list=sorted_surveys_list, history=True)


@surveys_bp.route('/todo-list', methods=['GET'])
@jwt_authorization(request)
def get_survey_todo_list(session):
    logger.info("Retrieving survey todo list")
    party_id = session.get('party_id')

    survey_list = party_controller.get_party_enabled_enrolments_details(party_id, 'todo')

    sorted_survey_list = sorted(survey_list, key=lambda k: k['return_by']['timestamp'], reverse=True)

    response = make_response(render_template('surveys/surveys-todo.html',
                                             just_added_case_id=request.args.get('case_id'),
                                             sorted_surveys_list=sorted_survey_list))

    # Ensure any return to list of surveys (e.g. browser back) round trips the server to display the latest statuses
    response.headers.set("Cache-Control", "no-cache, max-age=0, must-revalidate, no-store")

    return response
