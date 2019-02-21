
import logging

from flask import redirect, request, url_for, current_app as app
from structlog import wrap_logger
from frontstage.common.authorisation import jwt_authorization
from frontstage.common.cryptographer import Cryptographer
from frontstage.controllers import case_controller, collection_exercise_controller, iac_controller, party_controller
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
        iac = iac_controller.get_iac_from_enrolment(enrolment_code)

        # Add enrolment for user in party
        case_id = iac['caseId']
        case = case_controller.get_case_by_enrolment_code(enrolment_code)
        business_party_id = case['partyId']
        collection_exercise_id = case['caseGroup']['collectionExerciseId']
        # Get survey ID from collection Exercise
        added_survey_id = collection_exercise_controller.get_collection_exercise(
            case['caseGroup']['collectionExerciseId']).get('surveyId')

        info = party_controller.get_party_by_business_id(business_party_id, app.config['PARTY_URL'],
                                                                   app.config['PARTY_AUTH'], collection_exercise_id)

        already_enrolled = None
        if is_business_enrolled(info['associations'], case['caseGroup']['surveyId'], party_id):
            logger.info('User tried to enrol onto a survey they are already enrolled on',
                        case_id=case_id, party_id=party_id)
            already_enrolled = True
        else:
            case_controller.post_case_event(case_id,
                                            party_id=business_party_id,
                                            category='ACCESS_CODE_AUTHENTICATION_ATTEMPT',
                                            description='Access code authentication attempted')

            party_controller.add_survey(party_id, enrolment_code)

    except ApiError as exc:
        logger.error('Failed to assign user to a survey',
                     party_id=party_id, status_code=exc.status_code)
        raise

    logger.info('Successfully retrieved data for confirm add organisation/survey page',
                case_id=case_id, party_id=party_id)
    return redirect(url_for('surveys_bp.get_survey_list', _anchor=(business_party_id, added_survey_id), _external=True, business_party_id=business_party_id,
                            survey_id=added_survey_id, tag='todo', already_enrolled=already_enrolled))


def is_business_enrolled(associations, survey_id, party_id):
    """
    Makes two checks as a business can be enrolled  on a survey but not the respondent, which would causes a single
    check to break if another respondent from the business had previously enrolled on that survey

    :param associations: List of respondents and their enrolled surveys
    :param survey_id: id of the added survey
    :param party_id: id of the respondent
    :return: True if respondent and the business is enrolled on the survey and false otherwise
    """
    for info in associations:
        if info['partyId'] == party_id:
            for survey in info['enrolments']:
                if survey['surveyId'] == survey_id:
                    return True
    return False
