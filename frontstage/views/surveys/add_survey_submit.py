import json
import logging

from flask import redirect, request, url_for
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.authorisation import jwt_authorization
from frontstage.common.cryptographer import Cryptographer
from frontstage.exceptions.exceptions import ApiError
from frontstage.views.surveys import surveys_bp


logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route('/add-survey/add-survey-submit', methods=['GET'])
@jwt_authorization(request)
def add_survey_submit(session):
    party_id = session['party_id']
    logger.info('Assigning new survey to a user', party_id=party_id)

    cryptographer = Cryptographer()
    encrypted_enrolment_code = request.args.get('encrypted_enrolment_code')
    enrolment_code = cryptographer.decrypt(encrypted_enrolment_code.encode()).decode()
    json_params = {
        "enrolment_code": enrolment_code,
        "party_id": party_id
    }
    response = api_call('POST', app.config['ADD_SURVEY'], json=json_params)

    if response.status_code != 200:
        logger.error('Failed to assign user to a survey', status=response.status_code, party_id=party_id)
        raise ApiError(response)

    response_json = json.loads(response.text)
    case_id = response_json['case_id']

    logger.info('Successfully retrieved data for confirm add organisation/survey page', case_id=case_id,
                party_id=party_id)
    return redirect(url_for('surveys_bp.logged_in',
                            _theme='default',
                            _external=True,
                            case_id=case_id))
