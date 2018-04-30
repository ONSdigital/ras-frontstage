import logging
import json
from flask import render_template, request
from structlog import wrap_logger
from frontstage import app
from frontstage.common.authorisation import jwt_authorization
from frontstage.views.surveys import surveys_bp
from frontstage.common.api_call import api_call
from frontstage.exceptions.exceptions import ApiError

logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route('/upload_failed', methods=['GET'])
@jwt_authorization(request)
def upload_failed(session):
    case_id = request.args.get('case_id', None)
    party_id = session['party_id']
    error_info = request.args.get('error_info', None)
    params = {
        "party_id": party_id,
        "case_id": case_id
    }
    response = api_call('GET', app.config['ACCESS_CASE'], parameters=params)
    if response.status_code != 200:
        logger.error('Failed to retrieve case data', party_id=party_id, case_id=case_id, status=response.status_code)
        raise ApiError(response)
    case_data = json.loads(response.text)

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

    return render_template('surveys/surveys-upload-failure.html', survey_info=case_data['survey'],
                           collection_exercise_info=case_data['collection_exercise'], error_info=error_info, case_id=case_id)
