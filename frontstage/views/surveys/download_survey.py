import logging

from flask import request
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.authorisation import jwt_authorization
from frontstage.exceptions.exceptions import ApiError
from frontstage.views.surveys import surveys_bp


logger = wrap_logger(logging.getLogger(__name__))


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
        logger.error('Failed to download collection instrument', party_id=party_id, case_id=case_id,
                     status=response.status_code)
        raise ApiError(response)

    logger.info('Successfully downloaded collection instrument', case_id=case_id, party_id=party_id)
    return response.content, response.status_code, response.headers.items()
