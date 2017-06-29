import json
import logging
import requests
from flask import Blueprint, render_template, request, redirect, url_for, session
from jose import JWTError
from structlog import wrap_logger

from app.config import Config
from app.jwt import decode

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
    url = Config.API_GATEWAY_SURVEYS_URL + 'todo/' + party_id
    logger.debug("build_survey_data URL is: {}".format(url))
    req = requests.get(url, headers=headers, params=status_filter, verify=False)

    return req.json()


# ===== Surveys To Do =====
@surveys_bp.route('/', methods=['GET', 'POST'])
def logged_in():
    """Logged in page for users only."""

    if session.get('jwt_token'):
        jwttoken = session.get('jwt_token')

        try:
            decodedJWT = decode(jwttoken)
            for key in decodedJWT:
                logger.debug(" {} is: {}".format(key, decodedJWT[key]))

            # TODO: get user nane working
            # userID = decodedJWT['user_id']
            # return render_template('signed-in.html', _theme='default', data={"error": {"type": "success"}})
            # return render_template('surveys-history.html', _theme='default', data={"error": {"type": "success"}})

            # userID = decodedJWT['username']
            # userName = userID.split('@')[0]

            # Filters the data array to remove surveys that shouldn't appear on the To Do page
            status_filter = {'status_filter': '["not started", "in progress"]'}

            # Get the survey data (To Do survey type)
            data_array = build_survey_data(status_filter)

            # TODO: pass in data={"error": {"type": "success"}, "user_id": userName} to get the user name working ?
            return render_template('surveys-todo.html', _theme='default', data_array=data_array)

        except JWTError:
            # TODO Provide proper logging
            logger.error('This is not a valid JWT Token')

            # logger.warning('JWT scope could not be validated.')
            # TODO Provide proper logging
            logger.debug("This is not a valid JWT Token")
            # logger.warning('JWT scope could not be validated.')
            # Make sure we pop this invalid session variable.
            session.pop('jwt_token')

    return render_template('not-signed-in.html', _theme='default', data={"error": {"type": "failed"}})


# ===== Surveys History =====
@surveys_bp.route('/history')
def surveys_history():
    """Logged in page for users only."""

    if session.get('jwt_token'):
        jwttoken = session.get('jwt_token')

        try:
            decodedJWT = decode(jwttoken)
            for key in decodedJWT:
                logger.debug(" {} is: {}".format(key, decodedJWT[key]))

            # Filters the data array to remove surveys that shouldn't appear on the History page
            status_filter = {'status_filter': '["complete"]'}

            # Get the survey data (History survey type)
            data_array = build_survey_data(status_filter)

            # Render the template
            return render_template('surveys-history.html',  _theme='default', data_array=data_array)

        except JWTError:
            # TODO Provide proper logging
            logger.error('This is not a valid JWT Token')

            # logger.warning('JWT scope could not be validated.')
            # Make sure we pop this invalid session variable.
            session.pop('jwt_token')

    return render_template('not-signed-in.html', _theme='default', data={"error": {"type": "failed"}})


@surveys_bp.route('/access_survey', methods=['GET'])
def access_survey():
    """Logged in page for users only."""

    if session.get('jwt_token'):
        jwttoken = session.get('jwt_token')

        try:
            decodedJWT = decode(jwttoken)
            for key in decodedJWT:
                logger.debug(' {} is: {}'.format(key, decodedJWT[key]))

            case_id = request.args.get('case_id', None)
            collection_instrument_id = request.args.get('collection_instrument_id', None)

            url = Config.API_GATEWAY_COLLECTION_INSTRUMENT_URL + 'collectioninstrument/id/{}'.format(collection_instrument_id)
            logger.debug('Access_survey URL is: {}'.format(url))

            req = requests.get(url, verify=False)
            ci_data = req.json()

            # Render the template
            return render_template('surveys-access.html', _theme='default', case_id=case_id, ci_data=ci_data)

        except JWTError:
            # TODO Provide proper logging
            logger.error("This is not a valid JWT Token")

            # logger.warning('JWT scope could not be validated.')
            # Make sure we pop this invalid session variable.
            session.pop('jwt_token')
            return render_template('not-signed-in.html', _theme='default', data={"error": {"type": "failed"}})


@surveys_bp.route('/upload_survey', methods=['POST'])
def upload_survey():
    """Logged in page for users only."""

    case_id = request.args.get('case_id', None)

    if session.get('jwt_token'):
        jwttoken = session.get('jwt_token')

        try:
            decodedJWT = decode(jwttoken)
            for key in decodedJWT:
                logger.debug(' {} is: {}'.format(key, decodedJWT[key]))

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

        except JWTError:
            # TODO Provide proper logging
            logger.error("This is not a valid JWT Token")

            # Make sure we pop this invalid session variable.
            session.pop('jwt_token')
            return render_template('not-signed-in.html', _theme='default', data={"error": {"type": "failed"}})

        except Exception as e:
            logger.error("Error uploading survey response: {}", str(e))
            return redirect(url_for('error_page'))


@surveys_bp.route('/surveys-upload-failure', methods=['GET'])
def surveys_upload_failure():
    error_info = request.args.get('error_info', None)
    return render_template('surveys-upload-failure.html', _theme='default', error_info=error_info)
