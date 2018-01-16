import json
import logging
from os import getenv

from flask import Blueprint, redirect, render_template, request, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.authorisation import jwt_authorization
from frontstage.common.cryptographer import Cryptographer
from frontstage.exceptions.exceptions import ApiError
from frontstage.models import EnrolmentCodeForm

logger = wrap_logger(logging.getLogger(__name__))
surveys_bp = Blueprint('surveys_bp', __name__,
                       static_folder='static', template_folder='templates/surveys')
cryptographer = Cryptographer()


@surveys_bp.route('/', methods=['GET'])
@jwt_authorization(request)
def logged_in(session):
    party_id = session.get('party_id')
    surveys_list = get_surveys_list(party_id, 'todo')
    response = api_call('GET', app.config['CONFIRM_ADD_ORGANISATION_SURVEY'])
    template_data = {"survey": {"justAdded": "false"}}

    # Checks if new survey is added and renders "survey added" notification
    if response.status_code == 200:
        logger.info('New survey added to TODO')
        template_data = {"survey": {"justAdded": "true"}}
        return render_template('surveys/surveys-todo.html', _theme='default',
                               data=template_data, surveys_list=surveys_list)

    logger.info('No new survey added')
    return render_template('surveys/surveys-todo.html', data=template_data,
                           _theme='default', surveys_list=surveys_list)


@surveys_bp.route('/history', methods=['GET'])
@jwt_authorization(request)
def surveys_history(session):
    party_id = session['party_id']
    surveys_list = get_surveys_list(party_id, 'history')
    return render_template('surveys/surveys-history.html',  _theme='default',
                           surveys_list=surveys_list, history=True)


@surveys_bp.route('/add-survey', methods=['GET', 'POST'])
def add_survey():
    form = EnrolmentCodeForm(request.form)

    if request.method == 'POST' and form.validate():
        logger.info('Enrolment code submitted')
        enrolment_code = request.form.get('enrolment_code').lower()
        request_data = {
            'enrolment_code': enrolment_code,
            'initial': True
        }
        response = api_call('POST', app.config['VALIDATE_ENROLMENT'], json=request_data)

        # Handle API errors
        if response.status_code == 404:
            logger.info('Enrolment code not found')
            template_data = {"error": {"type": "failed"}}
            return render_template('surveys/surveys-add.html', _theme='default',
                                   form=form, data=template_data), 202
        elif response.status_code == 401 and not json.loads(response.text).get('active'):
            logger.info('Enrolment code not active')
            template_data = {"error": {"type": "failed"}}
            return render_template('surveys/surveys-add.html', _theme='default',
                                   form=form, data=template_data), 200
        elif response.status_code == 400 and not json.loads(response.text).get('used'):
            logger.info('Enrolment code already used')
            template_data = {"error": {"type": "failed"}}
            return render_template('surveys/surveys-add.html', _theme='default',
                                   form=form, data=template_data), 200
        elif response.status_code != 200:
            logger.error('Failed to submit enrolment code')
            raise ApiError(response)

        encrypted_enrolment_code = cryptographer.encrypt(enrolment_code.encode()).decode()
        logger.info('Successful enrolment code submitted')
        return redirect(url_for('surveys_bp.add_survey_confirm_organisation',
                                encrypted_enrolment_code=encrypted_enrolment_code,
                                _external=True,
                                _scheme=getenv('SCHEME', 'http')))

    return render_template('surveys/surveys-add.html', _theme='default',
                           form=form, data={"error": {}})


@surveys_bp.route('/add-survey/confirm-organisation-survey', methods=['GET'])
def add_survey_confirm_organisation():
    # Get and decrypt enrolment code
    encrypted_enrolment_code = request.args.get('encrypted_enrolment_code', None)
    enrolment_code = cryptographer.decrypt(encrypted_enrolment_code.encode()).decode()

    logger.info('Attempting to retrieve data for confirm add organisation/survey page')
    response = api_call('POST', app.config['CONFIRM_ADD_ORGANISATION_SURVEY'],
                        json={'enrolment_code': enrolment_code})

    if response.status_code != 200:
        logger.error('Failed to retrieve data for confirm add organisation/survey page')
        raise ApiError(response)

    response_json = json.loads(response.text)
    logger.info('Successfully retrieved data for confirm add organisation/survey page')
    return render_template('surveys/surveys-confirm-organisation.html',
                           _theme='default',
                           enrolment_code=enrolment_code,
                           encrypted_enrolment_code=encrypted_enrolment_code,
                           organisation_name=response_json['organisation_name'],
                           survey_name=response_json['survey_name'])


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
