import json
import logging

from flask import render_template, request
from structlog import wrap_logger

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.common.cryptographer import Cryptographer
from frontstage.exceptions.exceptions import ApiError
from frontstage.views.register import register_bp


logger = wrap_logger(logging.getLogger(__name__))


@register_bp.route('/create-account/confirm-organisation-survey', methods=['GET'])
def register_confirm_organisation_survey():
    # Get and decrypt enrolment code
    cryptographer = Cryptographer()
    encrypted_enrolment_code = request.args.get('encrypted_enrolment_code', None)
    enrolment_code = cryptographer.decrypt(encrypted_enrolment_code.encode()).decode()

    logger.info('Attempting to retrieve data for confirm organisation/survey page')
    response = api_call('POST', app.config['CONFIRM_ORGANISATION_SURVEY'],
                        json={'enrolment_code': enrolment_code})

    if response.status_code != 200:
        logger.error('Failed to retrieve data for confirm organisation/survey page')
        raise ApiError(response)

    response_json = json.loads(response.text)
    logger.info('Successfully retrieved data for confirm organisation/survey page')
    return render_template('register/register.confirm-organisation-survey.html',
                           enrolment_code=enrolment_code,
                           encrypted_enrolment_code=encrypted_enrolment_code,
                           organisation_name=response_json['organisation_name'],
                           survey_name=response_json['survey_name'])
