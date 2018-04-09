import json
import logging

from flask import redirect, render_template, request, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.authorisation import jwt_authorization
from frontstage.exceptions.exceptions import ApiError
from frontstage.views.surveys import surveys_bp


logger = wrap_logger(logging.getLogger(__name__))


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
                         status=response.status_code,
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
    return render_template('surveys/surveys-upload-success.html', upload_filename=upload_filename)
