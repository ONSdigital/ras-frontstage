import json
import logging

from flask import render_template, request, make_response
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.authorisation import jwt_authorization
from frontstage.exceptions.exceptions import ApiError
from frontstage.views.surveys import surveys_bp


logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route('/', methods=['GET'])
@jwt_authorization(request)
def logged_in(session):
    party_id = session.get('party_id')

    surveys_list = get_surveys_list(party_id, 'todo')
    sorted_surveys_list = sorted(surveys_list, key=lambda k: k['collection_exercise']['scheduledReturnDateTime'],
                                 reverse=True)

    response = make_response(render_template('surveys/surveys-todo.html',
                           just_added_case_id=request.args.get('case_id'),
                           _theme='default', sorted_surveys_list=sorted_surveys_list))

    # Ensure any return to list of surveys (e.g. browser back) round trips the server to display the latest statuses
    response.headers.set("Cache-Control", "no-cache, max-age=0, must-revalidate, no-store")

    return response

@surveys_bp.route('/history', methods=['GET'])
@jwt_authorization(request)
def surveys_history(session):
    party_id = session['party_id']
    sorted_surveys_list = get_surveys_list(party_id, 'history')
    return render_template('surveys/surveys-history.html', _theme='default',
                           sorted_surveys_list=sorted_surveys_list, history=True)


def get_surveys_list(party_id, list_type):
    logger.info('Retrieving surveys list', party_id=party_id, list_type=list_type)
    params = {
        "party_id": party_id,
        "list": list_type
    }
    response = api_call('GET', app.config['SURVEYS_LIST'], parameters=params)

    if response.status_code != 200:
        logger.error('Failed to retrieve surveys list', party_id=party_id, list_type=list_type,
                     status=response.status_code)
        raise ApiError(response)

    surveys_list = json.loads(response.text)
    logger.info('Successfully retrieved surveys list', party_id=party_id, list_type=list_type)
    return surveys_list
