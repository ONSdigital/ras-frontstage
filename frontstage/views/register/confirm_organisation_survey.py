import logging

from flask import render_template, request
from structlog import wrap_logger

from frontstage.common.cryptographer import Cryptographer
from frontstage.controllers import (case_controller, collection_exercise_controller,
                                    iac_controller, party_controller, survey_controller)
from frontstage.exceptions.exceptions import ApiError
from frontstage.views.register import register_bp


logger = wrap_logger(logging.getLogger(__name__))


@register_bp.route('/create-account/confirm-organisation-survey', methods=['GET'])
def register_confirm_organisation_survey():
    # Get and decrypt enrolment code
    cryptographer = Cryptographer()
    encrypted_enrolment_code = request.args.get('encrypted_enrolment_code', None)
    enrolment_code = cryptographer.decrypt(encrypted_enrolment_code.encode()).decode()
    # Validate enrolment code before retrieving organisation data
    iac_controller.validate_enrolment_code(enrolment_code)

    logger.info('Attempting to retrieve data for confirm organisation/survey page')
    try:
        # Get organisation name
        case = case_controller.get_case_by_enrolment_code(enrolment_code)
        business_party_id = case['caseGroup']['partyId']
        organisation_name = party_controller.get_party_by_business_id(business_party_id).get('name')

        # Get survey name
        collection_exercise_id = case['caseGroup']['collectionExerciseId']
        collection_exercise = collection_exercise_controller.get_collection_exercise(collection_exercise_id)
        survey_id = collection_exercise['surveyId']
        survey_name = survey_controller.get_survey(survey_id).get('longName')
    except ApiError as exc:
        logger.error('Failed to retrieve data for confirm organisation/survey page', status_code=exc.status_code)
        raise

    logger.info('Successfully retrieved data for confirm organisation/survey page')
    return render_template('register/register.confirm-organisation-survey.html',
                           encrypted_enrolment_code=encrypted_enrolment_code,
                           organisation_name=organisation_name,
                           survey_name=survey_name)
