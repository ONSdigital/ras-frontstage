import logging

from flask import render_template, request
from structlog import wrap_logger

from frontstage.common.authorisation import jwt_authorization
from frontstage.views.surveys import surveys_bp


logger = wrap_logger(logging.getLogger(__name__))


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

    return render_template('surveys/surveys-upload-failure.html', error_info=error_info, case_id=case_id)
