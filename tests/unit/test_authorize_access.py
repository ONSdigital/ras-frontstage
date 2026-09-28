import unittest
from unittest.mock import patch

from werkzeug.exceptions import BadRequest, Unauthorized

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
    def test_case_access_returns_true_when_authorized(
        self,
        get_survey_by_short_name,
        is_respondent_enrolled,
    ):
        get_survey_by_short_name.return_value = self.survey
        is_respondent_enrolled.return_value = True

        self.assertTrue(
            self.case_access.case_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                self.business_party_id,
                self.survey_short_name,
            )
        )

    @patch("frontstage.common.authorize_access.survey_controller.get_survey_by_short_name")
    def test_case_access_rejects_mismatched_business_party(
        self,
        get_survey_by_short_name,
    ):
        get_survey_by_short_name.return_value = self.survey

        with self.assertRaises(Unauthorized):
            self.case_access.case_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                "wrong-business",
                self.survey_short_name,
            )

    @patch("frontstage.common.authorize_access.survey_controller.get_survey_by_short_name")
    def test_case_access_rejects_mismatched_collection_exercise(
        self,
        get_survey_by_short_name,
    ):
        get_survey_by_short_name.return_value = self.survey

        with self.assertRaises(Unauthorized):
            self.case_access.case_access(
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
    def test_case_access_rejects_mismatched_survey(
        self,
        get_survey_by_short_name,
    ):
        get_survey_by_short_name.return_value = {
            "id": "wrong-survey",
            "shortName": self.survey_short_name,
        }

        with self.assertRaises(Unauthorized):
            self.case_access.case_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                self.business_party_id,
                self.survey_short_name,
            )

    @patch("frontstage.common.authorize_access.party_controller.is_respondent_enrolled")
    @patch("frontstage.common.authorize_access.survey_controller.get_survey_by_short_name")
    def test_case_access_rejects_not_enrolled(
        self,
        get_survey_by_short_name,
        is_respondent_enrolled,
    ):
        get_survey_by_short_name.return_value = self.survey
        is_respondent_enrolled.return_value = False

        with self.assertRaises(Unauthorized):
            self.case_access.case_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                self.business_party_id,
                self.survey_short_name,
            )

    @patch("frontstage.common.authorize_access.party_controller.is_respondent_enrolled")
    def test_check_permission_success(
        self,
        is_respondent_enrolled,
    ):
        is_respondent_enrolled.return_value = True

        self.assertIsNone(
            CaseAccess.check_permission(
                self.business_party_id,
                self.case_id,
                self.party_id,
                self.survey,
            )
        )

    @patch("frontstage.common.authorize_access.party_controller.is_respondent_enrolled")
    def test_check_permission_raises(
        self,
        is_respondent_enrolled,
    ):
        is_respondent_enrolled.return_value = False

        with self.assertRaises(NoSurveyPermission):
            CaseAccess.check_permission(
                self.business_party_id,
                self.case_id,
                self.party_id,
                self.survey,
            )

    def test_check_seft_success(self):
        self.assertIsNone(
            CaseAccess.check_seft(
                self.business_party_id,
                self.case["caseGroup"],
                self.survey_id,
            )
        )

    def test_check_seft_business_mismatch(self):
        with self.assertRaises(BadRequest):
            CaseAccess.check_seft(
                "wrong-business",
                self.case["caseGroup"],
                self.survey_id,
            )

    def test_check_seft_survey_mismatch(self):
        with self.assertRaises(BadRequest):
            CaseAccess.check_seft(
                self.business_party_id,
                self.case["caseGroup"],
                "wrong-survey",
            )
