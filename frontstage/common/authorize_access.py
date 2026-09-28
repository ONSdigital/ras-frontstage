import logging

from structlog import wrap_logger

from frontstage.controllers import (
    party_controller,
    survey_controller,
)
from frontstage.exceptions.exceptions import (
    NoSurveyPermission,
)

logger = wrap_logger(logging.getLogger(__name__))


class CaseAccess:

    def __init__(self):
        pass

    def case_access(self, case, collection_exercise, party_id, business_party_id, survey_short_name):
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
            raise NoSurveyPermission(party_id, case_id)

        if collection_exercise["id"] != case_collection_exercise_id:
            logger.warning(
                "Collection exercise does not belong to case",
                case_id=case_id,
                party_id=party_id,
                collection_exercise_id=collection_exercise["id"],
                case_collection_exercise_id=case_collection_exercise_id,
            )
            raise NoSurveyPermission(party_id, case_id)

        if survey["id"] != collection_exercise["surveyId"]:
            logger.warning(
                "Survey does not belong to collection exercise",
                case_id=case_id,
                party_id=party_id,
                supplied_survey_id=survey["id"],
                collection_exercise_survey_id=collection_exercise["surveyId"],
            )
            raise NoSurveyPermission(party_id, case_id)

        if not party_controller.is_respondent_enrolled(party_id, case_business_party_id, survey["id"]):
            logger.warning(
                "Respondent is not enrolled for case business and survey",
                case_id=case_id,
                party_id=party_id,
                business_party_id=case_business_party_id,
                survey_id=survey["id"],
            )
            raise NoSurveyPermission(party_id, case_id)
        return True
