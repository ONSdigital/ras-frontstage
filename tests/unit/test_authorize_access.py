import unittest
from unittest.mock import patch

from werkzeug.exceptions import Unauthorized

from frontstage.common.authorize_access import (
    authorize_access,
    check_enrollment,
)
from frontstage.exceptions.exceptions import NoSurveyPermission
from tests.integration.mocked_services import (
    business_party,
    case,
    collection_exercise,
    respondent_party,
    survey_eq,
)


class TestCaseAccess(unittest.TestCase):

    def setUp(self):

        self.case = {
            "id": "case-id",
            "caseGroup": {
                "partyId": "business-party-id",
                "collectionExerciseId": "collection-exercise-id",
                "surveyId": "survey-id",
            },
        }

        self.collection_exercise = {
            "id": "collection-exercise-id",
            "surveyId": "survey-id",
        }

        self.survey = {
            "id": "survey-id",
            "shortName": "QBS",
        }

        self.case_id = self.case["id"]
        self.party_id = "respondent-id"
        self.business_party_id = "business-party-id"
        self.survey_id = self.survey["id"]
        self.survey_short_name = self.survey["shortName"]

    @patch("frontstage.common.authorize_access.party_controller.is_respondent_enrolled")
    @patch("frontstage.common.authorize_access.survey_controller.get_survey_by_short_name")
    def test_authorize_access_returns_true_when_authorized(
        self,
        get_survey_by_short_name,
        is_respondent_enrolled,
    ):
        get_survey_by_short_name.return_value = self.survey
        is_respondent_enrolled.return_value = True

        self.assertTrue(
            authorize_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                self.business_party_id,
                self.survey_short_name,
            )
        )

    @patch("frontstage.common.authorize_access.survey_controller.get_survey_by_short_name")
    def test_authorize_access_rejects_mismatched_business_party(
        self,
        get_survey_by_short_name,
    ):
        get_survey_by_short_name.return_value = self.survey

        with self.assertRaises(Unauthorized):
            authorize_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                "wrong-business",
                self.survey_short_name,
            )

    @patch("frontstage.common.authorize_access.survey_controller.get_survey_by_short_name")
    def test_authorize_access_rejects_mismatched_collection_exercise(
        self,
        get_survey_by_short_name,
    ):
        get_survey_by_short_name.return_value = self.survey

        with self.assertRaises(Unauthorized):
            authorize_access(
                self.case,
                {
                    "id": "wrong-collection-exercise",
                    "surveyId": self.survey_id,
                },
                self.party_id,
                self.business_party_id,
                self.survey_short_name,
            )

    @patch("frontstage.common.authorize_access.survey_controller.get_survey_by_short_name")
    def test_authorize_access_rejects_mismatched_survey(
        self,
        get_survey_by_short_name,
    ):
        get_survey_by_short_name.return_value = {
            "id": "wrong-survey",
            "shortName": self.survey_short_name,
        }

        with self.assertRaises(Unauthorized):
            authorize_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                self.business_party_id,
                self.survey_short_name,
            )

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    @patch("frontstage.common.authorize_access." "survey_controller.get_survey_by_short_name")
    def test_authorize_access_rejects_not_enrolled(
        self,
        get_survey_by_short_name,
        is_respondent_enrolled,
    ):
        get_survey_by_short_name.return_value = survey_eq
        is_respondent_enrolled.return_value = False

        collection_exercise_copy = {
            **collection_exercise,
            "surveyId": survey_eq["id"],
        }

        case_copy = {
            **case,
            "caseGroup": {
                **case["caseGroup"],
                "partyId": business_party["id"],
            },
        }

        with self.assertRaises(NoSurveyPermission):
            authorize_access(
                case_copy,
                collection_exercise_copy,
                respondent_party["id"],
                business_party["id"],
                survey_eq["shortName"],
            )

        is_respondent_enrolled.assert_called_once_with(
            respondent_party["id"],
            business_party["id"],
            survey_eq["id"],
        )

    @patch("frontstage.common.authorize_access.party_controller.is_respondent_enrolled")
    def test_check_enrollment_success(
        self,
        is_respondent_enrolled,
    ):
        is_respondent_enrolled.return_value = True

        self.assertIsNone(
            check_enrollment(
                self.business_party_id,
                self.case_id,
                self.party_id,
                self.survey,
            )
        )

    @patch("frontstage.common.authorize_access.party_controller.is_respondent_enrolled")
    def test_check_enrollment_raises(
        self,
        is_respondent_enrolled,
    ):
        is_respondent_enrolled.return_value = False

        with self.assertRaises(NoSurveyPermission):
            check_enrollment(
                self.business_party_id,
                self.case_id,
                self.party_id,
                self.survey,
            )
