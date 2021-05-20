import logging

from flask import render_template, abort, request, url_for
from structlog import wrap_logger
from werkzeug.utils import redirect

from frontstage import app
from frontstage.common.authorisation import jwt_authorization
from frontstage.controllers import party_controller, survey_controller
from frontstage.controllers.party_controller import get_business_by_id
from frontstage.exceptions.exceptions import ApiError
from frontstage.views.account import account_bp

logger = wrap_logger(logging.getLogger(__name__))


@account_bp.route('/share-surveys/accept-share-surveys/<token>', methods=['GET'])
def get_share_survey_summary(token):
    logger.info('Getting share survey summary', token=token)
    try:
        response = party_controller.verify_share_survey_token(token)
        pending_share_surveys = response.json()
        share_dict = {}
        distinct_businesses = set()
        batch_number = pending_share_surveys[0]['batch_no']
        for pending_share_survey in pending_share_surveys:
            distinct_businesses.add(pending_share_survey['business_id'])
        for business_id in distinct_businesses:
            business_surveys = []
            for pending_share_survey in pending_share_surveys:
                if pending_share_survey['business_id'] == business_id:
                    business_surveys.append(survey_controller.get_survey(app.config['SURVEY_URL'],
                                                                         app.config['BASIC_AUTH'],
                                                                         pending_share_survey['survey_id']))
            selected_business = get_business_by_id(business_id)
            share_dict[selected_business[0]['name']] = {
                'trading_as': selected_business[0]['trading_as'],
                'surveys': business_surveys
            }
        return render_template('surveys/surveys-share/summary.html',
                               share_dict=share_dict,
                               batch_no=batch_number)

    except ApiError as exc:
        # Handle api errors
        if exc.status_code == 409:
            logger.info('Expired share survey email verification token', token=token, api_url=exc.url,
                        api_status_code=exc.status_code)
            abort(409)
        elif exc.status_code == 404:
            logger.warning('Unrecognised share survey email verification token', token=token, api_url=exc.url,
                           api_status_code=exc.status_code)
            abort(404)
        else:
            logger.info('Failed to verify share survey email', token=token, api_url=exc.url,
                        api_status_code=exc.status_code)
            raise exc


@account_bp.route('/confirm-share-surveys/<batch>', methods=['GET'])
@jwt_authorization(request)
def accept_share_surveys(session, batch):
    logger.info('Attempting to confirm share surveys', batch_number=batch)
    try:
        party_controller.confirm_share_survey(batch)
    except ApiError as exc:
        logger.error('Failed to confirm share survey', status=exc.status_code, batch_number=batch)
        raise exc
    logger.info('Successfully completed share survey', batch_number=batch)
    return redirect(url_for('surveys_bp.get_survey_list', tag='todo'))
