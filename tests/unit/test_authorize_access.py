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

        self.party_id = "respondent-id"
        self.business_party_id = "business-party-id"
        self.survey_short_name = "QBS"

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    @patch("frontstage.common.authorize_access." "survey_controller.get_survey_by_short_name")
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
            self.survey_short_name,
        )

        self.assertTrue(result)
        get_survey_by_short_name.assert_called_once_with(self.survey_short_name)
        is_respondent_enrolled.assert_called_once_with(
            self.party_id,
            self.business_party_id,
            self.survey["id"],
        )

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    @patch("frontstage.common.authorize_access." "survey_controller.get_survey_by_short_name")
    def test_case_access_rejects_mismatched_business_party(
        self,
        get_survey_by_short_name,
        is_respondent_enrolled,
    ):
        get_survey_by_short_name.return_value = self.survey

        with self.assertRaises(Unauthorized) as raised:
            self.case_access.case_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                "different-business-party-id",
                self.survey_short_name,
            )

        self.assertEqual(raised.exception.code, 401)
        is_respondent_enrolled.assert_not_called()

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    @patch("frontstage.common.authorize_access." "survey_controller.get_survey_by_short_name")
    def test_case_access_rejects_mismatched_collection_exercise(
        self,
        get_survey_by_short_name,
        is_respondent_enrolled,
    ):
        get_survey_by_short_name.return_value = self.survey
        collection_exercise = dict(self.collection_exercise)
        collection_exercise["id"] = "different-collection-exercise-id"

        with self.assertRaises(Unauthorized) as raised:
            self.case_access.case_access(
                self.case,
                collection_exercise,
                self.party_id,
                self.business_party_id,
                self.survey_short_name,
            )

        self.assertEqual(raised.exception.code, 401)
        is_respondent_enrolled.assert_not_called()

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    @patch("frontstage.common.authorize_access." "survey_controller.get_survey_by_short_name")
    def test_case_access_rejects_mismatched_survey(
        self,
        get_survey_by_short_name,
        is_respondent_enrolled,
    ):
        get_survey_by_short_name.return_value = {
            "id": "different-survey-id",
            "shortName": self.survey_short_name,
        }

        with self.assertRaises(Unauthorized) as raised:
            self.case_access.case_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                self.business_party_id,
                self.survey_short_name,
            )

        self.assertEqual(raised.exception.code, 401)
        is_respondent_enrolled.assert_not_called()

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    @patch("frontstage.common.authorize_access." "survey_controller.get_survey_by_short_name")
    def test_case_access_rejects_respondent_without_enrolment(
        self,
        get_survey_by_short_name,
        is_respondent_enrolled,
    ):
        get_survey_by_short_name.return_value = self.survey
        is_respondent_enrolled.return_value = False

        with self.assertRaises(Unauthorized) as raised:
            self.case_access.case_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                self.business_party_id,
                self.survey_short_name,
            )

        self.assertEqual(raised.exception.code, 401)
        is_respondent_enrolled.assert_called_once_with(
            self.party_id,
            self.business_party_id,
            self.survey["id"],
        )

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    def test_check_permission_success(self, is_respondent_enrolled):
        is_respondent_enrolled.return_value = True

        result = CaseAccess.check_permission(
            self.business_party_id,
            self.case["id"],
            self.party_id,
            self.survey,
        )

        self.assertIsNone(result)
        is_respondent_enrolled.assert_called_once_with(
            self.party_id,
            self.business_party_id,
            self.survey["id"],
        )

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    def test_check_permission_rejects_respondent_without_enrolment(
        self,
        is_respondent_enrolled,
    ):
        is_respondent_enrolled.return_value = False

        with self.assertRaises(NoSurveyPermission):
            CaseAccess.check_permission(
                self.business_party_id,
                self.case["id"],
                self.party_id,
                self.survey,
            )

        is_respondent_enrolled.assert_called_once_with(
            self.party_id,
            self.business_party_id,
            self.survey["id"],
        )

    def test_check_seft_success(self):
        result = CaseAccess.check_seft(
            self.business_party_id,
            self.case["caseGroup"],
            self.survey["id"],
        )

        self.assertIsNone(result)

    def test_check_seft_rejects_mismatched_business_party(self):
        with self.assertRaises(BadRequest) as raised:
            CaseAccess.check_seft(
                "different-business-party-id",
                self.case["caseGroup"],
                self.survey["id"],
            )

        self.assertEqual(raised.exception.code, 400)

    def test_check_seft_rejects_mismatched_survey(self):
        with self.assertRaises(BadRequest) as raised:
            CaseAccess.check_seft(
                self.business_party_id,
                self.case["caseGroup"],
                "different-survey-id",
            )

        self.assertEqual(raised.exception.code, 400)
