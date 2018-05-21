import logging

from flask import redirect, request, url_for
from structlog import wrap_logger

from frontstage.common.authorisation import jwt_authorization
from frontstage.common.cryptographer import Cryptographer
from frontstage.controllers import case_controller, iac_controller, party_controller
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

    try:
        # Verify enrolment code is active
        iac = iac_controller.get_iac_from_enrolment(enrolment_code, validate=True)

        case_id = iac['caseId']
        case = case_controller.get_case_by_enrolment_code(enrolment_code)
        case_group_id = case.get('caseGroup', {}).get('id')
        business_party_id = case['partyId']
        case_controller.post_case_event(case_id,
                                        party_id=business_party_id,
                                        category='ACCESS_CODE_AUTHENTICATION_ATTEMPT',
                                        description='Access code authentication attempted')

        party_controller.add_survey(party_id, enrolment_code)

        case_list = case_controller.get_cases_by_party_id(party_id)
        case_id = case_controller.get_case_id_for_group(case_list, case_group_id)
    except ApiError as exc:
        logger.error('Failed to assign user to a survey',
                     enrolment_code=enrolment_code, party_id=party_id, status_code=exc.status_code)
        raise

    logger.info('Successfully retrieved data for confirm add organisation/survey page',
                case_id=case_id, party_id=party_id)
    return redirect(url_for('surveys_bp.logged_in', _external=True, case_id=case_id))
