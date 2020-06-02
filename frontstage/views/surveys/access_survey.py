import logging

from flask import render_template, request, redirect
from structlog import wrap_logger

from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import case_controller, conversation_controller
from frontstage.views.surveys import surveys_bp


logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route('/access_survey', methods=['GET'])  # Deprecated , will be removed when no longer in use
@surveys_bp.route('/access-survey', methods=['GET'])
@jwt_authorization(request)
def access_survey(session):
    party_id = session['party_id']
    case_id = request.args['case_id']
    business_party_id = request.args['business_party_id']
    survey_short_name = request.args['survey_short_name']
    collection_instrument_type = request.args['ci_type']

    if collection_instrument_type == 'EQ':
        logger.info('Attempting to redirect to EQ', party_id=party_id, case_id=case_id)
        return redirect(case_controller.get_eq_url(case_id, party_id, business_party_id, survey_short_name))

    logger.info('Retrieving case data', party_id=party_id, case_id=case_id)
    referer_header = request.headers.get('referer', {})

    case_data = case_controller.get_case_data(case_id, party_id, business_party_id, survey_short_name)

    logger.info('Successfully retrieved case data', party_id=party_id, case_id=case_id)
    unread_message_count = { 'unread_message_count': conversation_controller.get_message_count(party_id) }
    return render_template('surveys/surveys-access.html', case_id=case_id,
                           collection_instrument_id=case_data['collection_instrument']['id'],
                           collection_instrument_size=case_data['collection_instrument']['len'],
                           survey_info=case_data['survey'],
                           collection_exercise_info=case_data['collection_exercise'],
                           business_info=case_data['business_party'],
                           referer_header=referer_header,
                           unread_message_count=unread_message_count)
