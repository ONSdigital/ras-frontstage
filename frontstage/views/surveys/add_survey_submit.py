import logging

from flask import abort
from flask import current_app as app
from flask import redirect, request, url_for
from structlog import wrap_logger

from frontstage.common.authorisation import jwt_authorization
from frontstage.common.cryptographer import Cryptographer
from frontstage.controllers import (
    case_controller,
    collection_exercise_controller,
    iac_controller,
    party_controller,
)
from frontstage.exceptions.exceptions import ApiError
from frontstage.views.surveys import surveys_bp

logger = wrap_logger(logging.getLogger(__name__))


@surveys_bp.route("/add-survey/add-survey-submit", methods=["GET"])
@jwt_authorization(request)
def add_survey_submit(session):
    party_id = session.get_party_id()

    cryptographer = Cryptographer()
    encrypted_enrolment_code = request.args.get("encrypted_enrolment_code")
    enrolment_code = cryptographer.decrypt(encrypted_enrolment_code.encode()).decode()
    logger.info("Assigning new survey to a user", party_id=party_id, enrolment_code=enrolment_code)

    try:
        # Verify enrolment code is active
        iac = iac_controller.get_iac_from_enrolment(enrolment_code)
        if iac is None:
            # Showing the client an error screen if the enrolment code is either not found or inactive isn't great
            # but it's better then what used to happen, which was raise TypeError and show them the generic exception
            # page.  This lets us more easily debug the issue.  Ideally we'd redirect the user to the surveys_list
            # page with a 'Something went wrong when signing you up for the survey, try again or call us' error.
            logger.error("IAC code not found or inactive", enrolment_code=enrolment_code)
            abort(400)

        # Add enrolment for user in party
        case_id = iac["caseId"]
        case = case_controller.get_case_by_enrolment_code(enrolment_code)
        business_party_id = case["partyId"]
        collection_exercise_id = case["caseGroup"]["collectionExerciseId"]
        # Get survey ID from collection Exercise
        added_survey_id = collection_exercise_controller.get_collection_exercise(
            case["caseGroup"]["collectionExerciseId"]
        ).get("surveyId")

        info = party_controller.get_party_by_business_id(
            business_party_id, app.config["PARTY_URL"], app.config["BASIC_AUTH"], collection_exercise_id
        )

        already_enrolled = None
        if is_respondent_and_business_enrolled(info["associations"], case["caseGroup"]["surveyId"], party_id):
            logger.info(
                "User tried to enrol onto a survey they are already enrolled on",
                case_id=case_id,
                party_id=party_id,
                enrolment_code=enrolment_code,
            )
            already_enrolled = True
        else:
            case_controller.post_case_event(
                case_id,
                party_id=business_party_id,
                category="ACCESS_CODE_AUTHENTICATION_ATTEMPT",
                description="Access code authentication attempted",
            )

            party_controller.add_survey(party_id, enrolment_code)
            logger.info(
                "Successful enrolment code submitted when attempting to add survey", enrolment_code=enrolment_code
            )

    except ApiError as exc:
        logger.error("Failed to assign user to a survey", party_id=party_id, status_code=exc.status_code)
        raise

    logger.info(
        "Successfully retrieved data for confirm add organisation/survey page",
        case_id=case_id,
        party_id=party_id,
        enrolment_code=enrolment_code,
    )
    return redirect(
        url_for(
            "surveys_bp.get_survey_list",
            _external=True,
            business_party_id=business_party_id,
            survey_id=added_survey_id,
            tag="todo",
            already_enrolled=already_enrolled,
        )
    )


def is_respondent_and_business_enrolled(associations, survey_id, party_id):
    """
    This function checks whether or not a respondent's associated party is associated with the survey. If yes,
    we then check if the survey_id of the survey we are trying to add is found within the enrolments of the respondent.
    We do this because a respondent can be responding on behalf of several businesses, and a business can have several
    people enrolled on the same survey.

    :param associations: List of respondents and their enrolled surveys
    :param survey_id: id of the added survey
    :param party_id: id of the respondent
    :return: True if respondent and the business is enrolled on the survey and false otherwise
    """
    for association in associations:
        if association["partyId"] == party_id:
            for survey in association["enrolments"]:
                if survey["surveyId"] == survey_id:
                    return True
    return False
