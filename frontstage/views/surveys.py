import logging

from flask import Blueprint, render_template, request
import requests
from structlog import wrap_logger

from frontstage import app
from frontstage.common.post_event import post_event
from frontstage.common.authorisation import jwt_authorization
from frontstage.exceptions.exceptions import ExternalServiceError


logger = wrap_logger(logging.getLogger(__name__))

surveys_bp = Blueprint('surveys_bp', __name__, static_folder='static', template_folder='templates/surveys')


def build_survey_data(session, status_filter):
    party_id = session.get('party_id', 'no-party-id')
    logger.debug('Retrieving survey data', party_id=party_id)
    url = app.config['RAS_AGGREGATOR_TODO'].format(app.config['RAS_API_GATEWAY_SERVICE'], party_id)
    req = requests.get(url, params=status_filter, verify=False)
    if req.status_code != 200:
        logger.error('Failed to retrieve survey')
        ExternalServiceError(req)
    return req.json()


# ===== Surveys To Do =====
@surveys_bp.route('/', methods=['GET', 'POST'])
@jwt_authorization(request)
def logged_in(session):
    """Logged in page for users only."""

    # Filters the data array to remove surveys that shouldn't appear on the To Do page
    status_filter = {'status_filter': '["not started", "in progress"]'}

    # Get the survey data (To Do survey type)
    data_array = build_survey_data(session, status_filter)

    return render_template('surveys/surveys-todo.html', _theme='default', data_array=data_array)


# ===== Surveys History =====
@surveys_bp.route('/history')
@jwt_authorization(request)
def surveys_history(session):
    """Logged in page for users only."""

    # Filters the data array to remove surveys that shouldn't appear on the History page
    status_filter = {'status_filter': '["complete"]'}

    # Get the survey data (History survey type)
    data_array = build_survey_data(session, status_filter)

    # Render the template
    return render_template('surveys/surveys-history.html',  _theme='default', data_array=data_array)


def get_cases_from_party(party_id):
    # Get cases for given party_id
    url = app.config['RM_CASE_GET_BY_PARTY'].format(app.config['RM_CASE_SERVICE'], party_id)
    req = requests.get(url, verify=False)
    if req.status_code != 200:
        logger.error('Failed to retrieve case', party_id=party_id)
        raise ExternalServiceError(req)
    logger.debug('Successfully read cases for party', party_id=party_id)
    return req.json()


def access_surveys_permissions(collection_instrument_id, party_id):
    logger.info('Collection instrument access requested',
                collection_instrument=collection_instrument_id,
                party_id=party_id)

    cases = get_cases_from_party(party_id)
    # Check if any case has matching collection instrument
    for case in cases:
        if case.get('collectionInstrumentId') == collection_instrument_id:
            logger.debug('Party has permission to access collection instrument',
                         party_id=party_id,
                         collection_instrument_id=collection_instrument_id)
            return True
    logger.warning('Party does not have permission to access collection_instrument',
                   party_id=party_id,
                   collection_instrument_id=collection_instrument_id)
    return False


def upload_surveys_permissions(case_id, party_id):
    logger.info('Collection instrument access requested',
                case=case_id,
                party_id=party_id)

    cases = get_cases_from_party(party_id)
    # Check if any case has matching id
    for case in cases:
        if case.get('id') == case_id:
            logger.debug('Party has permission to upload survey',
                         party_id=party_id,
                         collection_instrument_id=case_id)
            return True
    logger.warning('Party does not have permission to upload survey',
                   party_id=party_id,
                   case_id=case_id)
    return False


@surveys_bp.route('/access_survey', methods=['GET', 'POST'])
@jwt_authorization(request)
def access_survey(session):
    """Logged in page for users only."""
    party_id = session.get('party_id', 'no-party-id')

    # View survey information
    if request.method == 'POST':
        case_id = request.form.get('case_id', None)
        collection_instrument_id = request.form.get('collection_instrument_id', None)
        survey = request.form.get('survey', None)
        survey_abbr = request.form.get('survey_abbr', None)
        business = request.form.get('business', None)
        period_start = request.form.get('period_start', None)
        period_end = request.form.get('period_end', None)
        submit_by = request.form.get('submit_by', None)
        logger.info('Attempting to access survey information',
                    party_id=party_id,
                    collection_instrument_id=collection_instrument_id,
                    case_id=case_id)

        valid = access_surveys_permissions(collection_instrument_id, party_id)
        if not valid:
            return render_template("errors/error.html", _theme='default', data={"error": {"type": "failed"}})

        logger.info('Retrieving collection instrument',
                    party_id=party_id,
                    collection_instrument_id=collection_instrument_id)
        url = app.config['RAS_CI_GET'].format(app.config['RAS_COLLECTION_INSTRUMENT_SERVICE'], collection_instrument_id)
        req = requests.get(url, verify=False)
        if req.status_code != 200:
            logger.error('Failed to retrieve collection instrument',
                         collection_instrument_id=collection_instrument_id,
                         party_id=party_id)
            raise ExternalServiceError(req)
        ci_data = req.json()

        return render_template('surveys/surveys-access.html', _theme='default', case_id=case_id, ci_data=ci_data,
                               survey=survey, survey_abbr=survey_abbr, business=business, period_start=period_start,
                               period_end=period_end, submit_by=submit_by)

    # GET request here downloads the xlsx file
    if request.method == 'GET':
        collection_instrument_id = request.args.get('cid')
        case_id = request.args.get('case_id')
        logger.info('Attempting to download collection instrument',
                    party_id=party_id,
                    collection_instrument_id=collection_instrument_id,
                    case_id=case_id)

        valid = access_surveys_permissions(collection_instrument_id, party_id)
        if not valid:
            logger.warning('Party does not have permission to access collection instrument',
                           party_id=party_id,
                           collection_instrument_id=collection_instrument_id)
            return render_template("error.html", _theme='default', data={"error": {"type": "failed"}})

        logger.info('Attempting to download collection instrument',
                    party_id=party_id,
                    collection_instrument_id=collection_instrument_id)
        url = app.config['RAS_CI_DOWNLOAD'].format(app.config['RAS_COLLECTION_INSTRUMENT_SERVICE'],
                                                   collection_instrument_id)
        response = requests.get(url, verify=False)

        category = 'COLLECTION_INSTRUMENT_DOWNLOADED' if response.status_code == 200 else 'COLLECTION_INSTRUMENT_ERROR'
        code, msg = post_event(case_id,
                               category=category,
                               created_by='FRONTSTAGE',
                               party_id=party_id,
                               description='Instrument {} downloaded by {} for case {}'.format(collection_instrument_id, party_id, case_id))
        if code != 201:
            # Should we error out if the case post fails or let the user continue?
            logger.error('Failed to post case event',
                         error=msg,
                         status_code=code,
                         case_id=case_id,
                         category=category,
                         party_id=party_id)

        if response.status_code == 200:
            logger.info('Successfully downloaded collection instrument',
                        party_id=party_id,
                        collection_instrument_id=collection_instrument_id,
                        case_id=case_id)
            return response.content, response.status_code, response.headers.items()
        else:
            logger.error('Failed to download collection instrument',
                         collection_instrument_id=collection_instrument_id,
                         party_id=party_id,
                         status_code=response.status_code)
            return render_template('surveys/surveys-download-failure.html',
                                   _theme='default',
                                   error_info=request.args.get('error_info', None))


@surveys_bp.route('/upload_survey', methods=['POST'])
@jwt_authorization(request)
def upload_survey(session):
    """Logged in page for users only."""
    party_id = session.get('party_id', 'no-party-id')
    case_id = request.args.get('case_id', None)
    logger.info('Attempting to upload survey', party_id=party_id, case_id=case_id)

    valid = upload_surveys_permissions(case_id, party_id)
    if not valid:
        logger.warning('Party does not have permission to upload survey',
                       party_id=party_id,
                       case_id=case_id)
        return render_template("errors/error.html", _theme='default', data={"error": {"type": "failed"}})

    # Get the uploaded file
    upload_file = request.files['file']
    upload_filename = upload_file.filename
    upload_file = {'file': (upload_filename, upload_file.stream, upload_file.mimetype, {'Expires': 0})}

    # Upload the survey
    url = app.config['RAS_CI_UPLOAD'].format(app.config['RAS_COLLECTION_INSTRUMENT_SERVICE'], case_id)
    logger.info('Attempting to upload survey', url=url, case_id=case_id, party_id=party_id)
    result = requests.post(url, files=upload_file, verify=False)
    logger.debug('Upload survey response', result=result.status_code, reason=result.reason, text=result.text)

    category = 'SUCCESSFUL_RESPONSE_UPLOAD' if result.status_code == 200 else 'UNSUCCESSFUL_RESPONSE_UPLOAD'
    code, msg = post_event(case_id,
                           category=category,
                           created_by='FRONTSTAGE',
                           party_id=party_id,
                           description='Survey response for case {} uploaded by {}'.format(case_id, party_id))
    if code != 201:
        logger.error('Failed to post case event',
                     error=msg,
                     status_code=code,
                     case_id=case_id,
                     category=category,
                     party_id=party_id)

    if result.status_code == 200:
        logger.info('Upload successful', party_id=party_id, case_id=case_id)
        return render_template('surveys/surveys-upload-success.html', _theme='default', upload_filename=upload_filename)
    else:
        logger.error('Upload failed', status_code=result.status_code, party_id=party_id, case_id=case_id)
        error_info = {'status code': result.status_code, 'text': result.text}
        return render_template('surveys/surveys-upload-failure.html', _theme='default', error_info=error_info, case_id=case_id)
