import logging

from flask import abort
from structlog import wrap_logger

from frontstage.controllers import (
    party_controller,
    survey_controller,
)
from frontstage.exceptions.exceptions import (
    NoSurveyPermission,
)

logger = wrap_logger(logging.getLogger(__name__))


def case_access(case, collection_exercise, party_id, business_party_id, survey_short_name):
    """Authorize EQ access using relationships derived from the fetched case."""
    case_id = case["id"]
    case_business_party_id = case["caseGroup"]["partyId"]
    case_collection_exercise_id = case["caseGroup"]["collectionExerciseId"]
    survey = survey_controller.get_survey_by_short_name(survey_short_name)

    if business_party_id != case_business_party_id:
        logger.warning(
            "Supplied business does not belong to case",
            case_id=case_id,
            party_id=party_id,
            supplied_business_party_id=business_party_id,
            case_business_party_id=case_business_party_id,
        )
        abort(401)

    if collection_exercise["id"] != case_collection_exercise_id:
        logger.warning(
            "Collection exercise does not belong to case",
            case_id=case_id,
            party_id=party_id,
            collection_exercise_id=collection_exercise["id"],
            case_collection_exercise_id=case_collection_exercise_id,
        )
        abort(401)

    if survey["id"] != collection_exercise["surveyId"]:
        logger.warning(
            "Survey does not belong to collection exercise",
            case_id=case_id,
            party_id=party_id,
            supplied_survey_id=survey["id"],
            collection_exercise_survey_id=collection_exercise["surveyId"],
        )
        abort(401)
    check_enrollment(business_party_id, case_id, party_id, survey)
    return True


def check_enrollment(business_party_id, case_id, party_id, survey):
    if not party_controller.is_respondent_enrolled(party_id, business_party_id, survey["id"]):
        raise NoSurveyPermission(party_id, case_id)


def check_seft(business_party_id, case_group, survey_id):
    if business_party_id != case_group["partyId"]:
        logger.error(
            f"business_party_id {business_party_id} does not match case_group['partyId'] {case_group['partyId']}"
        )
        abort(400)
    if survey_id != case_group["surveyId"]:
        logger.error(f"survey_id {survey_id} and case_group['surveyId'] {case_group['surveyId']}")
        abort(400)
