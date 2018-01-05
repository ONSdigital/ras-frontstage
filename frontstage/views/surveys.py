import json
import logging

from flask import Blueprint, redirect, render_template, request, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.authorisation import jwt_authorization
from frontstage.exceptions.exceptions import ApiError


logger = wrap_logger(logging.getLogger(__name__))
surveys_bp = Blueprint('surveys_bp', __name__,
                       static_folder='static', template_folder='templates/surveys')


@surveys_bp.route('/', methods=['GET'])
@jwt_authorization(request)
def logged_in(session):
    party_id = session.get('party_id')
    surveys_list = get_surveys_list(party_id, 'todo')
    return render_template('surveys/surveys-todo.html', _theme='default', surveys_list=surveys_list)


@surveys_bp.route('/history', methods=['GET'])
@jwt_authorization(request)
def surveys_history(session):
    party_id = session['party_id']
    surveys_list = get_surveys_list(party_id, 'history')
    return render_template('surveys/surveys-history.html',  _theme='default',
                           surveys_list=surveys_list, history=True)


@surveys_bp.route('/add_survey', methods=['GET'])
@jwt_authorization(request)
def add_survey(session):
    party_id = session['party_id']
    surveys_list = get_surveys_list(party_id, 'history')
    return render_template('surveys/surveys-add.html', _theme='default')


def get_surveys_list(party_id, list_type):
    logger.info('Retrieving surveys list', party_id=party_id, list_type=list_type)
    params = {
        "party_id": party_id,
        "list": list_type
    }
    response = api_call('GET', app.config['SURVEYS_LIST'], parameters=params)

    if response.status_code != 200:
        logger.error('Failed to retrieve surveys list', party_id=party_id, list_type=list_type)
        raise ApiError(response)

    surveys_list = json.loads(response.text)
    logger.info('Successfully retrieved surveys list', party_id=party_id, list_type=list_type)
    return surveys_list


@surveys_bp.route('/access_survey', methods=['GET'])
@jwt_authorization(request)
def access_survey(session):
    party_id = session['party_id']
    case_id = request.args['case_id']
    referer_header = request.headers.get('referer', {})
    logger.info('Retrieving case data', party_id=party_id, case_id=case_id)
    params = {
        "party_id": party_id,
        "case_id": case_id
    }
    response = api_call('GET', app.config['ACCESS_CASE'], parameters=params)

    if response.status_code != 200:
        logger.error('Failed to retrieve case data', party_id=party_id, case_id=case_id)
        raise ApiError(response)
    case_data = json.loads(response.text)

    logger.info('Successfully retrieved case data', party_id=party_id, case_id=case_id)
    return render_template('surveys/surveys-access.html', _theme='default',
                           case_id=case_id,
                           collection_instrument_id=case_data['case']['collectionInstrumentId'],
                           collection_instrument_size=case_data['collection_instrument_size'],
                           survey_info=case_data['survey'],
                           collection_exercise_info=case_data['collection_exercise'],
                           business_info=case_data['business_party'],
                           referer_header=referer_header)


@surveys_bp.route('/download_survey', methods=['GET'])
@jwt_authorization(request)
def download_survey(session):
    party_id = session['party_id']
    case_id = request.args['case_id']
    logger.info('Downloading collection instrument', case_id=case_id, party_id=party_id)
    params = {
        "case_id": case_id,
        "party_id": party_id
    }
    response = api_call('GET', app.config['DOWNLOAD_CI'], parameters=params)

    if response.status_code != 200:
        logger.error('Failed to download collection instrument', party_id=party_id, case_id=case_id)
        raise ApiError(response)

    logger.info('Successfully downloaded collection instrument', case_id=case_id, party_id=party_id)
    return response.content, response.status_code, response.headers.items()


@surveys_bp.route('/upload_survey', methods=['POST'])
@jwt_authorization(request)
def upload_survey(session):
    party_id = session['party_id']
    case_id = request.args['case_id']
    logger.info('Uploading collection instrument', party_id=party_id, case_id=case_id)

    if request.content_length > app.config['MAX_UPLOAD_LENGTH']:
        return redirect(url_for('surveys_bp.upload_failed',
                                _external=True,
                                case_id=case_id,
                                error_info='size'))

    # Get the uploaded file
    upload_file = request.files['file']
    upload_filename = upload_file.filename
    upload_file = {
        'file': (upload_filename, upload_file.stream, upload_file.mimetype, {'Expires': 0})
    }
    params = {
        "case_id": case_id,
        "party_id": party_id
    }
    response = api_call('POST', app.config['UPLOAD_CI'], files=upload_file, parameters=params)

    # Handle specific error messages from frontstage-api
    if response.status_code == 400:
        error_message = json.loads(response.text).get('error', {}).get('data', {}).get('message')
        if ".xlsx format" in error_message:
            error_info = "type"
        elif "50 characters" in error_message:
            error_info = "charLimit"
        elif "File too large" in error_message:
            error_info = 'size'
        else:
            logger.error('Unexpected error message returned from collection instrument',
                         status_code=response.status_code,
                         error_message=error_message,
                         party_id=party_id,
                         case_id=case_id)
            error_info = "unexpected"
        return redirect(url_for('surveys_bp.upload_failed',
                                _external=True,
                                case_id=case_id,
                                error_info=error_info))
    elif response.status_code != 200:
        logger.error('Failed to upload collection instrument', party_id=party_id, case_id=case_id)
        raise ApiError(response)

    logger.info('Successfully uploaded collection instrument', party_id=party_id, case_id=case_id)
    return render_template('surveys/surveys-upload-success.html',
                           _theme='default', upload_filename=upload_filename)


@surveys_bp.route('/upload_failed', methods=['GET'])
@jwt_authorization(request)
def upload_failed(session):
    case_id = request.args.get('case_id', None)
    error_info = request.args.get('error_info', None)

    # Select correct error text depending on error_info
    if error_info == "type":
        error_info = {'header': "Error uploading - incorrect file type",
                      'body': 'The spreadsheet must be in .xls or .xlsx format'}
    elif error_info == "charLimit":
        error_info = {'header': "Error uploading - file name too long",
                      'body': 'The file name of your spreadsheet must be '
                              'less than 50 characters long'}
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
