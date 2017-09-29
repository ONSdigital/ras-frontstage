import logging
from os import getenv

import arrow
from flask import Blueprint, render_template, request, url_for
import requests
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage import app
from frontstage.common.post_event import post_event
from frontstage.common.authorisation import jwt_authorization
from frontstage.exceptions.exceptions import ExternalServiceError


logger = wrap_logger(logging.getLogger(__name__))

surveys_bp = Blueprint('surveys_bp', __name__, static_folder='static', template_folder='templates/surveys')


# ===== Surveys To Do =====
@surveys_bp.route('/', methods=['GET'])
@jwt_authorization(request)
def logged_in(session):
    status_filter = ["not started", "in progress"]
    data_array = build_surveys_data(session, status_filter)
    return render_template('surveys/surveys-todo.html', _theme='default', data_array=data_array)


# ===== Surveys History =====
@surveys_bp.route('/history', methods=['GET'])
@jwt_authorization(request)
def surveys_history(session):
    status_filter = ["complete"]
    data_array = build_surveys_data(session, status_filter)
    return render_template('surveys/surveys-history.html',  _theme='default', data_array=data_array, history=True)


@surveys_bp.route('/access_survey', methods=['GET'])
@jwt_authorization(request)
def access_survey(session):
    party_id = session.get('party_id', 'no-party-id')
    case_id = request.args.get('case_id', None)
    loggerb = logger.bind(party_id=party_id, case_id=case_id)
    referer_header = request.headers['referer']

    # Retrieving and parsing data for given case
    survey_data = build_single_survey_data(case_id=case_id, logger=loggerb)

    # Confirming current user has permission to access case data
    case_party_id = survey_data.get('case').get('partyId')
    valid = access_surveys_permissions(party_id, case_party_id, loggerb)
    if not valid:
        return render_template("errors/error.html", _theme='default', data={"error": {"type": "failed"}})

    # Parse survey data
    survey_info = survey_data.get('survey')
    collection_exercise_info = survey_data.get('collection_exercise')
    business_info = survey_data.get('business_party')
    collection_instrument_id = survey_data.get('case').get('collectionInstrumentId')
    collection_instrument_size = get_collection_instrument_size(collection_instrument_id, loggerb)

    return render_template('surveys/surveys-access.html', _theme='default',
                           case_id=case_id,
                           collection_instrument_id=collection_instrument_id,
                           collection_instrument_size=collection_instrument_size,
                           survey_info=survey_info,
                           collection_exercise_info=collection_exercise_info,
                           business_info=business_info, referer_header=referer_header)


@surveys_bp.route('/download_survey', methods=['GET'])
@jwt_authorization(request)
def download_survey(session):
    party_id = session.get('party_id', 'no-party-id')
    collection_instrument_id = request.args.get('cid')
    case_id = request.args.get('case_id')
    loggerb = logger.bind(party_id=party_id, collection_instrument_id=collection_instrument_id, case_id=case_id)
    case = get_case(case_id, loggerb)
    case_party_id = case.get('partyId')

    valid = access_surveys_permissions(party_id, case_party_id, loggerb)
    if not valid:
        return render_template("errors/error.html", _theme='default', data={"error": {"type": "failed"}})

    collection_instrument, status_code, headers = download_collection_instrument(collection_instrument_id, logger)
    post_download_collection_instrument_case_event(case_id, party_id, collection_instrument_id, status_code)

    if status_code == 200:
        logger.info('Successfully downloaded collection instrument', collection_instrument_id=collection_instrument_id)
        return collection_instrument, status_code, headers
    else:
        logger.error('Failed to download collection instrument', status_code=status_code)
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

    if request.content_length > app.config['MAX_UPLOAD_LENGTH']:
        error_info = "size"

        return redirect(url_for('surveys_bp.upload_failed',
                                _external=True,
                                _scheme=getenv('SCHEME', 'http'),
                                case_id=case_id,
                                error_info=error_info))

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
    logger.info('Attempting to upload survey', case_id=case_id, party_id=party_id)
    url = app.config['RAS_CI_UPLOAD'].format(app.config['RAS_COLLECTION_INSTRUMENT_SERVICE'], case_id)
    result = requests.post(url, auth=app.config['BASIC_AUTH'], files=upload_file, verify=False)
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
        if ".xlsx format" in result.text:
            error_info = "type"
        elif "50 characters" in result.text:
            error_info = "charLimit"
        else:
            logger.error('Unexpected error message returned from collection instrument',
                         status_code=result.status_code,
                         party_id=party_id,
                         case_id=case_id)
            error_info = "unexpected"

        return redirect(url_for('surveys_bp.upload_failed',
                                _external=True,
                                _scheme=getenv('SCHEME', 'http'),
                                case_id=case_id,
                                error_info=error_info))


@surveys_bp.route('/upload_failed', methods=['GET'])
@jwt_authorization(request)
def upload_failed(session):
    """Logged in page for users only."""
    party_id = session.get('party_id', 'no-party-id')
    case_id = request.args.get('case_id', None)
    error_info = request.args.get('error_info', None)
    logger.error('Upload failed', party_id=party_id, case_id=case_id)

    if error_info == "type":
        error_info = {'header': "Error uploading - incorrect file type",
                      'body': 'The spreadsheet must be in .xls or .xlsx format'}
    elif error_info == "charLimit":
        error_info = {'header': "Error uploading - file name too long",
                      'body': 'The file name of your spreadsheet must be less than 50 characters long'}
    elif error_info == "size":
        error_info = {'header': "Error uploading - file size too large",
                      'body': 'The spreadsheet must be smaller than 20MB in size'}
    else:
        error_info = {'header': "Something went wrong",
                      'body': 'Please try uploading your spreadsheet again'}

    return render_template('surveys/surveys-upload-failure.html',
                           _theme='default',
                           error_info=error_info,
                           case_id=case_id)


def build_surveys_data(session, status_filter):
    party_id = session.get('party_id', 'no-party-id')
    cases = get_cases_from_party(party_id)
    filtered_cases = [case for case in cases if calculate_case_status(case).lower() in status_filter]
    surveys_data = [build_single_survey_data(case=case, status_filter=status_filter[0], logger=logger) for case in filtered_cases]
    return {'rows': surveys_data}


def build_single_survey_data(case_id=None, case=None, status_filter=None, logger=None):
    if case:
        case_id = case['id']
    elif case_id:
        case = get_case(case_id, logger)
    logger.debug('Attempting to build survey data', case_id=case_id)
    collection_exercise_id = case["caseGroup"]["collectionExerciseId"]
    collection_exercise = get_collection_exercise(collection_exercise_id, logger)
    collection_exercise_formatted = format_collection_exercise_dates(collection_exercise)
    business_party_id = case['caseGroup']['partyId']
    business_party = get_business_party(business_party_id, logger)
    survey_id = collection_exercise['surveyId']
    survey = get_survey(survey_id, logger)
    survey_data = {
        "case": case,
        "collection_exercise": collection_exercise_formatted,
        "business_party": business_party,
        "survey": survey,
        'status': status_filter
    }
    logger.debug('Successfully built survey data', case_id=case_id)
    return survey_data


def get_case(case_id, logger):
    logger.debug('Attempting to retrieve case', case_id=case_id)
    url = app.config['RM_CASE_GET'].format(app.config['RM_CASE_SERVICE'], case_id)
    response = requests.get(url, auth=app.config['BASIC_AUTH'])
    if response.status_code != 200:
        logger.error('Failed to retrieve case', case_id=case_id)
        raise ExternalServiceError(response)
    case = response.json()
    logger.debug('Successfully retrieved case', case_id=case_id)
    return case


def get_collection_exercise(collection_exercise_id, logger):
    logger.debug('Attempting to retrieve collection exercise', collection_exercise_id=collection_exercise_id)
    url = app.config['RM_COLLECTION_EXERCISES_GET'].format(app.config['RM_COLLECTION_EXERCISE_SERVICE'], collection_exercise_id)
    response = requests.get(url, auth=app.config['BASIC_AUTH'])
    if response.status_code != 200:
        logger.error('Failed to retrieve collection exercise', collection_exercise_id=collection_exercise_id)
        raise ExternalServiceError(response)
    collection_exercise = response.json()
    logger.debug('Successfully retrieved collection exercise', collection_exercise_id=collection_exercise_id)
    return collection_exercise


def format_collection_exercise_dates(collection_exercise):
    input_date_format = 'YYYY-MM-DDThh:mm:ss'
    output_date_format = 'D MMM YYYY'
    for key in ['periodStartDateTime', 'periodEndDateTime', 'scheduledReturnDateTime']:
        collection_exercise[key] = collection_exercise[key].replace('Z', '')
        collection_exercise[key + 'Formatted'] = arrow.get(collection_exercise[key], input_date_format).format(output_date_format)
    return collection_exercise


def get_business_party(business_party_id, logger):
    logger.debug('Attempting to retrieve business_party', business_party_id=business_party_id)
    url = app.config['RAS_PARTY_GET_BY_BUSINESS'].format(app.config['RAS_PARTY_SERVICE'], business_party_id)
    response = requests.get(url, auth=app.config['BASIC_AUTH'])
    if response.status_code != 200:
        logger.error('Failed to retrieve business party', business_party_id=business_party_id)
        raise ExternalServiceError(response)
    business_party = response.json()
    logger.debug('Successfully retrieved business party', business_party_id=business_party_id)
    return business_party


def get_survey(survey_id, logger):
    logger.debug('Attempting to retrieve survey', survey_id=survey_id)
    url = app.config['RM_SURVEY_GET'].format(app.config['RM_SURVEY_SERVICE'], survey_id)
    response = requests.get(url, auth=app.config['BASIC_AUTH'])
    if response.status_code != 200:
        logger.error('Failed to retrieve survey', survey_id=survey_id)
        raise ExternalServiceError(response)
    survey = response.json()
    logger.debug('Successfully retrieved survey', survey_id=survey_id)
    return survey


def calculate_case_status(case):
    case_events = case.get('caseEvents')
    status = None
    if case_events:
        for event in case_events:
            if event['category'] == 'SUCCESSFUL_RESPONSE_UPLOAD':
                status = 'Complete'
                break
            if event['category'] == 'COLLECTION_INSTRUMENT_DOWNLOADED':
                status = 'In Progress'
    return status if status else 'Not Started'


def get_collection_instrument_size(collection_instrument_id, logger):
    logger.debug('Attempting to retrieve collection instrument size', collection_instrument_id=collection_instrument_id)
    url = app.config['RAS_CI_SIZE'].format(app.config['RAS_COLLECTION_INSTRUMENT_SERVICE'], collection_instrument_id)
    response = requests.get(url, auth=app.config['BASIC_AUTH'], verify=False)
    if response.status_code != 200:
        logger.error('Failed to retrieve collection instrument size', collection_instrument_id=collection_instrument_id)
        raise ExternalServiceError(response)
    collection_instrument_size = response.json().get('size')
    logger.debug('Successfully retrieved collection instrument size', collection_instrument_id=collection_instrument_id)
    return collection_instrument_size


def download_collection_instrument(collection_instrument_id, logger):
    logger.info('Attempting to download collection instrument', collection_instrument_id=collection_instrument_id)
    url = app.config['RAS_CI_DOWNLOAD'].format(app.config['RAS_COLLECTION_INSTRUMENT_SERVICE'],
                                               collection_instrument_id)
    response = requests.get(url, auth=app.config['BASIC_AUTH'], verify=False)
    return response.content, response.status_code, response.headers.items()


def post_download_collection_instrument_case_event(case_id, party_id, collection_instrument_id, status_code):
    category = 'COLLECTION_INSTRUMENT_DOWNLOADED' if status_code == 200 else 'COLLECTION_INSTRUMENT_ERROR'
    code, msg = post_event(case_id,
                           category=category,
                           created_by='FRONTSTAGE',
                           party_id=party_id,
                           description='Instrument {} downloaded by {} for case {}'.format(collection_instrument_id, party_id, case_id))
    if code == 201:
        logger.debug('Successfully posted case',
                     error=msg,
                     status_code=code,
                     case_id=case_id,
                     category=category,
                     party_id=party_id)


def get_cases_from_party(party_id):
    logger.debug('Attempting to retrieve cases for party', party_id=party_id)
    url = app.config['RM_CASE_GET_BY_PARTY'].format(app.config['RM_CASE_SERVICE'], party_id, 'caseevents=true')
    response = requests.get(url, auth=app.config['BASIC_AUTH'], verify=False)
    if response.status_code != 200:
        logger.error('Failed to retrieve cases', party_id=party_id)
        raise ExternalServiceError(response)
    logger.debug('Successfully read cases for party', party_id=party_id)
    cases = response.json()
    return cases


def access_surveys_permissions(party_id, case_party_id, logger):
    logger.info('Collection instrument access requested',
                party_id=party_id,
                case_party_id=case_party_id)
    if party_id != case_party_id:
        logger.warning('Party does not have permission to access collection instrument',
                       party_id=party_id,
                       case_party_id=case_party_id)
        return False
    else:
        logger.debug('Party has permission to access collection instrument',
                     party_id=party_id,
                     case_party_id=case_party_id)
        return True


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