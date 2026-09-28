import unittest
from unittest.mock import patch

from frontstage.common.authorize_access import CaseAccess
from frontstage.exceptions.exceptions import NoSurveyPermission


class TestCaseAccess(unittest.TestCase):

    def setUp(self):
        self.case_access = CaseAccess()

        self.case = {
            "id": "case-id",
            "caseGroup": {
                "partyId": "business-party-id",
                "collectionExerciseId": "collection-exercise-id",
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

        self.party_id = "respondent-id"
        self.business_party_id = "business-party-id"

    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    @patch("frontstage.controllers.survey_controller.get_survey_by_short_name")
    def test_case_access_success(
        self,
        get_survey_by_short_name,
        is_respondent_enrolled,
    ):
        get_survey_by_short_name.return_value = self.survey
        is_respondent_enrolled.return_value = True

        result = self.case_access.case_access(
            self.case,
            self.collection_exercise,
            self.party_id,
            self.business_party_id,
            "QBS",
        )

        self.assertTrue(result)

        get_survey_by_short_name.assert_called_once_with("QBS")

        is_respondent_enrolled.assert_called_once_with(
            self.party_id,
            self.business_party_id,
            self.survey["id"],
        )

    @patch("frontstage.controllers.survey_controller.get_survey_by_short_name")
    def test_case_access_business_party_mismatch(
        self,
        get_survey_by_short_name,
    ):
        get_survey_by_short_name.return_value = self.survey

        with self.assertRaises(NoSurveyPermission):
            self.case_access.case_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                "different-business-party-id",
                "QBS",
            )

    @patch("frontstage.controllers.survey_controller.get_survey_by_short_name")
    def test_case_access_collection_exercise_mismatch(
        self,
        get_survey_by_short_name,
    ):
        get_survey_by_short_name.return_value = self.survey

        collection_exercise = dict(self.collection_exercise)
        collection_exercise["id"] = "different-collection-exercise-id"

        with self.assertRaises(NoSurveyPermission):
            self.case_access.case_access(
                self.case,
                collection_exercise,
                self.party_id,
                self.business_party_id,
                "QBS",
            )

    @patch("frontstage.controllers.survey_controller.get_survey_by_short_name")
    def test_case_access_survey_mismatch(
        self,
        get_survey_by_short_name,
    ):
        get_survey_by_short_name.return_value = {
            "id": "different-survey-id",
            "shortName": "QBS",
        }

        with self.assertRaises(NoSurveyPermission):
            self.case_access.case_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                self.business_party_id,
                "QBS",
            )

    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    @patch("frontstage.controllers.survey_controller.get_survey_by_short_name")
    def test_case_access_respondent_not_enrolled(
        self,
        get_survey_by_short_name,
        is_respondent_enrolled,
    ):
        get_survey_by_short_name.return_value = self.survey
        is_respondent_enrolled.return_value = False

        with self.assertRaises(NoSurveyPermission):
            self.case_access.case_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                self.business_party_id,
                "QBS",
            )

        is_respondent_enrolled.assert_called_once_with(
            self.party_id,
            self.business_party_id,
            self.survey["id"],
        )
