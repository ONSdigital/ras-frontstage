import logging

from flask import request
from structlog import wrap_logger

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import case_controller, collection_instrument_controller, party_controller
from frontstage.views.surveys import surveys_bp


logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route('/download-survey', methods=['GET'])
@jwt_authorization(request)
def download_survey(session):
    party_id = session['party_id']
    case_id = request.args['case_id']
    business_party_id = request.args['business_party_id']
    survey_short_name = request.args['survey_short_name']
    logger.info('Attempting to download collection instrument', case_id=case_id, party_id=party_id)

    # Check if respondent has permission to download for this case
    case = case_controller.get_case_by_case_id(case_id)
    party_controller.is_respondent_enrolled(party_id, business_party_id, survey_short_name)

    collection_instrument, headers = collection_instrument_controller.download_collection_instrument(case['collectionInstrumentId'], case_id, party_id)

    logger.info('Successfully downloaded collection instrument', case_id=case_id, party_id=party_id)

    return collection_instrument, 200, headers
