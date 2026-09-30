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


def authorize_access(case, collection_exercise, party_id, business_party_id, survey_short_name, survey):
    case_id = case["id"]
    case_business_party_id = case["caseGroup"]["partyId"]
    case_collection_exercise_id = case["caseGroup"]["collectionExerciseId"]

    if business_party_id != case_business_party_id:
        logger.warning(
            "Supplied business does not belong to case",
            case_id=case_id,
            party_id=party_id,
            supplied_business_party_id=business_party_id,
            case_business_party_id=case_business_party_id,
        )
        abort(400)

    if collection_exercise["id"] != case_collection_exercise_id:
        logger.warning(
            "Collection exercise does not belong to case",
            case_id=case_id,
            party_id=party_id,
            collection_exercise_id=collection_exercise["id"],
            case_collection_exercise_id=case_collection_exercise_id,
        )
        abort(400)

    if survey["id"] != collection_exercise["surveyId"]:
        logger.warning(
            "Survey does not belong to collection exercise",
            case_id=case_id,
            party_id=party_id,
            supplied_survey_id=survey["id"],
            collection_exercise_survey_id=collection_exercise["surveyId"],
        )
        abort(400)
    check_enrollment(business_party_id, case_id, party_id, survey)
    return True


def check_enrollment(business_party_id, case_id, party_id, survey):
    if not party_controller.is_respondent_enrolled(party_id, business_party_id, survey["id"]):
        raise NoSurveyPermission(party_id, case_id)
