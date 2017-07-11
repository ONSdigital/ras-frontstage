import json
import logging
import requests
from flask import Blueprint, render_template, request, redirect, url_for
from structlog import wrap_logger
from ons_ras_common.ons_decorators import jwt_session
from ons_ras_common import ons_env
from app.config import Config

logger = wrap_logger(logging.getLogger(__name__))
surveys_bp = Blueprint('surveys_bp', __name__, static_folder='static', template_folder='templates')


def my_surveys_page(session, not_started=False, in_progress=False, complete=False):
    """
    Call the aggregated call to build an appropriate data array, then feed it into
    the "my-surveys" template.

    :param session: The users's current session record
    :param not_started: Are we interested in jobs that haven't started
    :param in_progress: Are we interested in jobs that are in progress
    :param complete: Are we interested in jobs that are complete
    :return: a rendered response
    """
    party_id = session.get('party_id', None)
    filter = []
    if not_started:
        filter.append('no started')
    if in_progress:
        filter.append('in progress')
    if complete:
        filter.append('complete')
    try:
        data = ons_env.case_service.my_surveys(party_id, str(filter))
        return render_template('surveys-todo.html', _theme='default', data_array=data)
    except Exception as e:
        ons_env.logger.error('unexpected error "{}"'.format(e))
        return redirect(url_for('error_page'))


def build_survey_data(party_id, status_filter):
    """Helper method used to query for Surveys (To Do and History)"""
    # TODO - Derive the Party Id
    # Call the API Gateway Service to get the To Do survey list
    url = Config.API_GATEWAY_AGGREGATED_SURVEYS_URL + 'todo/' + party_id
    req = requests.get(url, params=status_filter, verify=False)
    try:
        return req.json()
    except Exception as e:
        print(str(e))
        return []

# ===== Surveys To Do =====
@surveys_bp.route('/', methods=['GET', 'POST'])
@jwt_session(request)
def logged_in(session):
    """Logged in page for users only."""
    party_id = session.get('party_id', 'no-party-id')
    status_filter = {'status_filter': '["not started", "in progress"]'}
    data_array = build_survey_data(party_id, status_filter)
    # TODO: pass in data={"error": {"type": "success"}, "user_id": userName} to get the user name working ?
    return render_template('surveys-todo.html', _theme='default', data_array=data_array)


# ===== Surveys History =====
@surveys_bp.route('/history')
@jwt_session(request)
def surveys_history(session):
    return my_surveys_page(session, complete=True)

    #party_id = session.get('party_id', 'no-party-id')
    #status_filter = {'status_filter': '["complete"]'}
    #data_array = build_survey_data(party_id, status_filter)
    #return render_template('surveys-history.html',  _theme='default', data_array=data_array)

not_logged_in = {
    'file': 'not-signed-in.html',
    'error': {"error": {"type": "failed"}}
}


@surveys_bp.route('/access_survey', methods=['GET', 'POST'])
@jwt_session(request)
def access_survey(session):
    """Logged in page for users only."""
    instrument_id = request.form.get('collection_instrument_id', None)
    case_id = request.form.get('case_id', None)
    code, instrument = ons_env.collection_instrument.get_by_id(instrument_id)
    if code != 200:
        return redirect(url_for('error_page'))
    return render_template('surveys-access.html', _theme='default', case_id=case_id,
                           form=request.form, ci_data=instrument['instrument'])


@surveys_bp.route('/upload_survey', methods=['POST'])
@jwt_session(request)
def upload_survey(session):
    """Logged in page for users only."""
    party_id = session.get('party_id', 'no-party-id')
    case_id = request.args.get('case_id', None)
    try:
        file_obj = request.files['file']
    except Exception as e:
        print(e)
        raise Exception

    code, msg = ons_env.collection_instrument.upload(case_id, party_id, file_obj)
    if code == 200:
        logger.debug('Upload successful')
        return render_template('surveys-upload-success.html', _theme='default', upload_filename=file_obj.filename)

    return render_template('surveys-upload-failure.html',  _theme='default', error_info=msg, case_id=case_id)


@surveys_bp.route('/surveys-upload-failure', methods=['GET'])
def surveys_upload_failure():
    error_info = request.args.get('error_info', None)
    return render_template('surveys-upload-failure.html', _theme='default', error_info=error_info)
