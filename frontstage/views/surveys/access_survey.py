import json
import logging

from flask import render_template, request
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.authorisation import jwt_authorization
from frontstage.exceptions.exceptions import ApiError
from frontstage.views.surveys import surveys_bp


logger = wrap_logger(logging.getLogger(__name__))


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
        logger.error('Failed to retrieve case data', party_id=party_id, case_id=case_id, status=response.status_code)
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
