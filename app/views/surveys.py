import json
import logging
import requests

from flask import Blueprint, render_template, request
from ons_ras_common.ons_decorators import jwt_session
from structlog import wrap_logger

from app.config import Config
from ..common.post_event import post_event

logger = wrap_logger(logging.getLogger(__name__))
surveys_bp = Blueprint('surveys_bp', __name__, static_folder='static', template_folder='templates/surveys')


def build_survey_data(session, status_filter):
    """Helper method used to query for Surveys (To Do and History)"""

    # #done# TODO - Derive the Party Id
    # party_id = "3b136c4b-7a14-4904-9e01-13364dd7b972"
    party_id = session.get('party_id', 'no-party-id')

    # TODO - Add security headers
    # headers = {'authorization': jwttoken}
    headers = {}

    # Call the API Gateway Service to get the To Do survey list
    # url = Config.API_GATEWAY_AGGREGATED_SURVEYS_URL + 'todo/' + party_id

    url = Config.RAS_AGGREGATOR_TODO.format(Config.RAS_API_GATEWAY_SERVICE, session.get('party_id'))
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
    data_array = build_survey_data(session, status_filter)

    return render_template('surveys/surveys-todo.html', _theme='default', data_array=data_array)


# ===== Surveys History =====
@surveys_bp.route('/history')
@jwt_session(request)
def surveys_history(session):
    """Logged in page for users only."""

    # Filters the data array to remove surveys that shouldn't appear on the History page
    status_filter = {'status_filter': '["complete"]'}

    # Get the survey data (History survey type)
    data_array = build_survey_data(session, status_filter)

    # Render the template
    return render_template('surveys/surveys-history.html',  _theme='default', data_array=data_array)


@surveys_bp.route('/access_survey', methods=['GET', 'POST'])
@jwt_session(request)
def access_survey(session):
    """Logged in page for users only."""
    # TODO: this is totally insecure as it doesn't validate the user is allowed access
    #       to the passed collection_instrument_id

    party_id = session.get('party_id', 'no-party-id')

    # UPLOAD instrument response
    if request.method == 'POST':
        case_id = request.form.get('case_id', None)
        collection_instrument_id = request.form.get('collection_instrument_id', None)
        survey = request.form.get('survey', None)
        survey_abbr = request.form.get('survey_abbr', None)
        business = request.form.get('business', None)
        period_start = request.form.get('period_start', None)
        period_end = request.form.get('period_end', None)
        submit_by = request.form.get('submit_by', None)
        #
        #   Need a check here to make sure that party_id is allowed to access collection_instrument_id
        #   - we can do this by calling "get cases by party" and ensuring the instrument_id is in the result set
        #
        url = Config.RM_CASE_GET_BY_PARTY.format(Config.RM_CASE_SERVICE, party_id)
        req = requests.get(url, verify=False)
        if req.status_code != 200:
            logger.error('unable to lookup cases for party "{}"'.format(party_id))
            return render_template("error.html", _theme='default', data={"error": {"type": "failed"}})

        logger.debug('successfully read cases for party "{}"'.format(party_id))
        valid = False
        for case in req.json():
            if case.get('collectionInstrumentId') == collection_instrument_id:
                logger.debug('matched case to collection_instrument_id "{}"'.format(collection_instrument_id))
                valid = True
                break

        if not valid:
            logger.error('party "{}" does not have access to instrument "{}"'.format(party_id, collection_instrument_id))
            return render_template("error.html", _theme='default', data={"error": {"type": "failed"}})

        url = Config.RAS_CI_GET.format(Config.RAS_COLLECTION_INSTRUMENT_SERVICE, collection_instrument_id)
        logger.debug('Access_survey URL is: {}'.format(url))
        req = requests.get(url, verify=False)
        ci_data = req.json()

        # Render the template
        return render_template('surveys/surveys-access.html', _theme='default', case_id=case_id, ci_data=ci_data,
                               survey=survey, survey_abbr=survey_abbr, business=business, period_start=period_start,
                               period_end=period_end, submit_by=submit_by)

    # GET request here downloads the xlsx file
    if request.method == 'GET':
        collection_instrument_id = request.args.get('cid')
        case_id = request.args.get('case_id')
        #url = Config.API_GATEWAY_COLLECTION_INSTRUMENT_URL + 'download/' + collection_instrument_id

        url = Config.RAS_CI_DOWNLOAD.format(Config.RAS_COLLECTION_INSTRUMENT_SERVICE, collection_instrument_id)
        logger.info("Requesting spreadsheet file", collection_instrument=collection_instrument_id)
        response = requests.get(url, verify=False)

        category = 'COLLECTION_INSTRUMENT_DOWNLOADED' if response.status_code == 200 else 'COLLECTION_INSTRUMENT_ERROR'
        code, msg = post_event(case_id,
                               category=category,
                               created_by='SYSTEM',
                               party_id=party_id,
                               description='Instrument response uploaded "{}"'.format(case_id))
        if code != 201:
            logger.error('error "{}" logging case event'.format(code))
            logger.error(str(msg))

        if response.status_code == 200:
            return response.content, response.status_code, response.headers.items()
        else:
            # TODO Decide how to handle this error
            logger.error('ci download of "{}" failed with "{}"'.format(collection_instrument_id, response.status_code))
            return render_template("error.html", _theme='default', data={"error": {"type": "failed"}})


@surveys_bp.route('/upload_survey', methods=['POST'])
@jwt_session(request)
def upload_survey(session):
    """Logged in page for users only."""

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
    #url = Config.API_GATEWAY_COLLECTION_INSTRUMENT_URL + 'survey_responses/{}'.format(case_id)


    url = Config.RAS_CI_UPLOAD.format(Config.RAS_COLLECTION_INSTRUMENT_SERVICE, case_id)
    logger.debug('upload_survey URL is: {}'.format(url))

    # Call the API Gateway Service to upload the selected file
    result = requests.post(url, headers, files=upload_file, verify=False)
    logger.debug('Result => {} {} : {}'.format(result.status_code, result.reason, result.text))

    category = 'SUCCESSFUL_RESPONSE_UPLOAD' if result.status_code == 200 else 'UNSUCCESSFUL_RESPONSE_UPLOAD'
    code, msg = post_event(case_id,
                              category=category,
                              created_by='SYSTEM',
                              party_id=party_id,
                              description='Instrument response uploaded "{}"'.format(case_id))
    if code != 201:
        logger.error('error "{}" logging case event'.format(code))
        logger.error(str(msg))

    if result.status_code == 200:
        logger.debug('Upload successful')
        return render_template('surveys/surveys-upload-success.html', _theme='default', upload_filename=upload_filename)
    else:
        logger.debug('Upload failed')
        error_info = json.loads(result.text)
        return render_template('surveys/surveys-upload-failure.html',  _theme='default', error_info=error_info,
                               case_id=case_id)


@surveys_bp.route('/surveys-upload-failure', methods=['GET'])
def surveys_upload_failure():
    error_info = request.args.get('error_info', None)
    return render_template('surveys/surveys-upload-failure.html', _theme='default', error_info=error_info)
