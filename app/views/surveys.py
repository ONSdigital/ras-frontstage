import json
import logging
import requests
from flask import Blueprint, render_template, request, redirect, url_for #, session
from structlog import wrap_logger
from ons_ras_common.ons_decorators import jwt_session
from ons_ras_common import ons_env
from app.config import Config

logger = wrap_logger(logging.getLogger(__name__))
surveys_bp = Blueprint('surveys_bp', __name__, static_folder='static', template_folder='templates')


def build_survey_data(status_filter):
    """Helper method used to query for Surveys (To Do and History)"""

    # TODO - Derive the Party Id
    party_id = "3b136c4b-7a14-4904-9e01-13364dd7b972"

    # TODO - Add security headers
    # headers = {'authorization': jwttoken}
    headers = {}

    # Call the API Gateway Service to get the To Do survey list
    url = Config.API_GATEWAY_AGGREGATED_SURVEYS_URL + 'todo/' + party_id
    logger.debug("build_survey_data URL is: {}".format(url))
    req = requests.get(url, headers=headers, params=status_filter, verify=False)

    return req.json()


# ===== Surveys To Do =====
@surveys_bp.route('/', methods=['GET', 'POST'])
@jwt_session(request)
def logged_in(session):
    """Logged in page for users only."""

    # Filters the data array to remove surveys that shouldn't appear on the To Do page
    status_filter = {'status_filter': '["not started", "in progress"]'}
    # Get the survey data (To Do survey type)
    data_array = build_survey_data(status_filter)
    # TODO: pass in data={"error": {"type": "success"}, "user_id": userName} to get the user name working ?
    return render_template('surveys-todo.html', _theme='default', data_array=data_array)


# ===== Surveys History =====
@surveys_bp.route('/history')
@jwt_session(request)
def surveys_history(session):
    """Logged in page for users only."""

    # Filters the data array to remove surveys that shouldn't appear on the History page
    status_filter = {'status_filter': '["complete"]'}

    # Get the survey data (History survey type)
    data_array = build_survey_data(status_filter)

    # Render the template
    return render_template('surveys-history.html',  _theme='default', data_array=data_array)

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

    case_id = request.args.get('case_id', None)

    # TODO - Add security headers
    # headers = {'authorization': jwttoken}
    headers = {}

    # Get the uploaded file
    upload_file = request.files['file']
    upload_filename = upload_file.filename
    upload_file = {'file': (upload_filename, upload_file.stream, upload_file.mimetype, {'Expires': 0})}

    # Build the URL
    url = Config.API_GATEWAY_COLLECTION_INSTRUMENT_URL + 'survey_responses/{}'.format(case_id)
    logger.debug('upload_survey URL is: {}'.format(url))

    # Call the API Gateway Service to upload the selected file
    result = requests.post(url, headers, files=upload_file, verify=False)
    logger.debug('Result => {} {} : {}'.format(result.status_code, result.reason, result.text))

    if result.status_code == 200:
        logger.debug('Upload successful')
        return render_template('surveys-upload-success.html', _theme='default', upload_filename=upload_filename)
    else:
        logger.debug('Upload failed')
        error_info = json.loads(result.text)
        return render_template('surveys-upload-failure.html',  _theme='default', error_info=error_info,
                               case_id=case_id)

@surveys_bp.route('/surveys-upload-failure', methods=['GET'])
def surveys_upload_failure():
    error_info = request.args.get('error_info', None)
    return render_template('surveys-upload-failure.html', _theme='default', error_info=error_info)
