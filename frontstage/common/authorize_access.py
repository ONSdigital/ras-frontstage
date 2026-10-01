import logging

from flask import abort
from structlog import wrap_logger

from frontstage.controllers import (
    party_controller,
)
from frontstage.exceptions.exceptions import (
    NoSurveyPermission,
)

logger = wrap_logger(logging.getLogger(__name__))


def authorize_access(case, collection_exercise, party_id, business_party_id, survey_id):
    case_id = case["id"]
    case_business_party_id = case["caseGroup"]["partyId"]

    if business_party_id != case_business_party_id:
        logger.warning(
            "Supplied business does not belong to case",
            case_id=case_id,
            party_id=party_id,
            supplied_business_party_id=business_party_id,
            case_business_party_id=case_business_party_id,
        )
        abort(400)

    if survey_id != collection_exercise["surveyId"]:
        logger.warning(
            "Survey does not belong to collection exercise",
            case_id=case_id,
            party_id=party_id,
            supplied_survey_id=survey_id,
            collection_exercise_survey_id=collection_exercise["surveyId"],
        )
        abort(400)
    check_enrollment(business_party_id, case_id, party_id, survey_id)
    return True


def check_enrollment(business_party_id, case_id, party_id, survey_id):
    if not party_controller.is_respondent_enrolled(party_id, business_party_id, survey_id):
        raise NoSurveyPermission(party_id, case_id)
