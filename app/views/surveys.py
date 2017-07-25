"""

   Frontstage (my)Surveys Module
   License: MIT
   Copyright (c) 2017 Crown Copyright (Office for National Statistics)

"""
import json
import requests
from flask import Blueprint, render_template, request, redirect, url_for
from app.config import Config
from ons_ras_common.ons_decorators import jwt_session
from ons_ras_common import ons_env
from ..post_event import post_event

surveys_bp = Blueprint('surveys_bp', __name__, static_folder='static', template_folder='templates')

CI_GET = '{}collection-instrument-api/1.0.2/collectioninstrument/id/{}'
CI_UPLOAD = '{}collection-instrument-api/1.0.2/survey_responses/{}'
AGGREGATOR_TODO = '{}api/1.0.0/surveys/todo/{}'

@surveys_bp.route('/', methods=['GET', 'POST'])
@jwt_session(request)
def logged_in(session):
    """
    Display the todo tab for the 'my surveys' page

    :param session: The user's current session details
    :return: A rendered version of the my surveys page
    """
    return my_surveys_page(session, page='surveys-todo.html', in_progress=True, not_started=True)


@surveys_bp.route('/history')
@jwt_session(request)
def surveys_history(session):
    """
    Display the history tab for the 'my surveys' page

    :param session: The user's current session details
    :return: A rendered version of the my surveys page
    """
    return my_surveys_page(session, page='surveys-history.html', complete=True)


@surveys_bp.route('/access_survey', methods=['GET', 'POST'])
@jwt_session(request)
def access_survey(session):
    """
    Come here when a user clicks on the 'access survey' button.

    :param session: The user's current session details
    :return: The survey-access page for the selected survey
    """
    instrument_id = request.form.get('collection_instrument_id', None)
    case_id = request.form.get('case_id', None)

    url = CI_GET.format(Config.RAS_COLLECTION_INSTRUMENT_SERVICE, instrument_id)
    ons_env.logger.debug('calling "{}"'.format(url))
    req = requests.get(url)
    if req.status_code != 200:
        return redirect(url_for('error_page'))
    instrument = json.loads(req.text)
    return render_template('surveys-access.html', _theme='default', case_id=case_id, form=request.form, ci_data=instrument)


@surveys_bp.route('/upload_survey', methods=['POST'])
@jwt_session(request)
def upload_survey(session):
    """
    Handle a user upload of a returning instrument.

    :param session: The user's current session details
    :return: Renders a success or failure page
    """
    party_id = session.get('party_id', 'no-party-id')
    case_id = request.args.get('case_id', None)

    # TODO - Add security headers
    # headers = {'authorization': jwttoken}
    headers = {}

    # Get the uploaded file
    upload_file = request.files['file']
    upload_filename = upload_file.filename
    upload_file = {'file': (upload_filename, upload_file.stream, upload_file.mimetype, {'Expires': 0})}

    # Build the URL
    url = CI_UPLOAD.format(Config.RAS_COLLECTION_INSTRUMENT_SERVICE, case_id)
    ons_env.logger.debug('upload_survey URL is: {}'.format(url))

    # Call the API Gateway Service to upload the selected file
    result = requests.post(url, headers, files=upload_file, verify=False)
    ons_env.logger.debug('Result => {} {} : {}'.format(result.status_code, result.reason, result.text))

    category = 'SUCCESSFUL_RESPONSE_UPLOAD' if result.status_code == 200 else 'UNSUCCESSFUL_RESPONSE_UPLOAD'
    code, msg = post_event(case_id,
                              category=category,
                              created_by='SYSTEM',
                              party_id=party_id,
                              description='Instrument response uploaded "{}"'.format(case_id))
    if code != 200:
        ons_env.logger.error('error code = {} logging to case service: "{}"'.format(code, msg['text']))
    if result.status_code:
        ons_env.logger.debug('Upload successful')
        return render_template('surveys-upload-success.html', _theme='default', upload_filename=upload_filename)
    else:
        ons_env.logger.debug('Upload failed')
        error_info = json.loads(result.text)
        return render_template('surveys-upload-failure.html', _theme='default', error_info=error_info, case_id=case_id)



def my_surveys_page(session, page=None, not_started=False, in_progress=False, complete=False):
    """
    Call the aggregated call to build an appropriate data array, then feed it into
    the "my-surveys" template.

    :param session: The users's current session record
    :param page: The page to render
    :param not_started: Are we interested in jobs that haven't started
    :param in_progress: Are we interested in jobs that are in progress
    :param complete: Are we interested in jobs that are complete
    :return: a rendered response
    """
    filter = []
    if not_started:
        filter.append("not started")
    if in_progress:
        filter.append("in progress")
    if complete:
        filter.append("complete")
    try:
        status_filter = {'status_filter': json.dumps(filter)}
        url = AGGREGATOR_TODO.format(Config.RAS_API_GATEWAY_SERVICE, session.get('party_id'))
        ons_env.logger.debug('calling "{}"'.format(url))
        req = requests.get(url, params=status_filter)
        if req.status_code != 200:
            ons_env.logger.error(json.loads(req.text))
            return redirect(url_for('error_page'))
        return render_template(page, _theme='default', data_array=req.json())
    except Exception as e:
        ons_env.logger.error('unexpected error "{}"'.format(e))
        return redirect(url_for('error_page'))

