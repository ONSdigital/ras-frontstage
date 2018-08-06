import logging

from flask import redirect, render_template, request, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import case_controller, collection_instrument_controller
from frontstage.exceptions.exceptions import CiUploadError
from frontstage.views.surveys import surveys_bp


logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route('/upload_survey', methods=['POST'])
@jwt_authorization(request)
def upload_survey(session):
    party_id = session['party_id']
    case_id = request.args['case_id']
    business_party_id = request.args['business_party_id']
    survey_short_name = request.args['survey_short_name']
    logger.info('Attempting to upload collection instrument', case_id=case_id, party_id=party_id)

    if request.content_length > app.config['MAX_UPLOAD_LENGTH']:
        return redirect(url_for('surveys_bp.upload_failed',
                                _external=True,
                                case_id=case_id,
                                business_party_id=business_party_id,
                                survey_short_name=survey_short_name,
                                error_info='size'))

    # Check if respondent has permission to upload for this case
    case_controller.check_case_permissions(party_id, case_id, business_party_id, survey_short_name)

    # Get the uploaded file
    upload_file = request.files['file']
    upload_filename = upload_file.filename
    upload_file = {
        'file': (upload_filename, upload_file.stream, upload_file.mimetype, {'Expires': 0})
    }

    try:
        # Upload the file to the collection instrument service
        collection_instrument_controller.upload_collection_instrument(upload_file, case_id, party_id)
    except CiUploadError as ex:
        if ".xlsx format" in ex.error_message:
            error_info = "type"
        elif "50 characters" in ex.error_message:
            error_info = "charLimit"
        elif "File too large" in ex.error_message:
            error_info = 'size'
        else:
            logger.error('Unexpected error message returned from collection instrument service',
                         status=ex.status_code,
                         error_message=ex.error_message,
                         party_id=party_id,
                         case_id=case_id)
            error_info = "unexpected"
        return redirect(url_for('surveys_bp.upload_failed',
                                _external=True,
                                case_id=case_id,
                                error_info=error_info))

    logger.info('Successfully uploaded collection instrument', party_id=party_id, case_id=case_id)
    return render_template('surveys/surveys-upload-success.html', upload_filename=upload_filename)
