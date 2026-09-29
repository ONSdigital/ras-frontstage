import unittest
from unittest.mock import patch

from werkzeug.exceptions import BadRequest, Unauthorized

from frontstage.common.authorize_access import case_access, check_enrollment, check_seft
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

        self.case_id = case["id"]
        self.party_id = respondent_party["id"]
        self.business_party_id = business_party["id"]
        self.survey_id = survey_eq["id"]
        self.survey_short_name = survey_eq["shortName"]

        self.case = {
            **case,
            "caseGroup": {
                **case["caseGroup"],
                "partyId": self.business_party_id,
                "collectionExerciseId": collection_exercise["id"],
                "surveyId": self.survey_id,
            },
        }

        self.collection_exercise = {
            **collection_exercise,
            "surveyId": self.survey_id,
        }

        self.survey = {
            **survey_eq,
        }

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    @patch("frontstage.common.authorize_access." "survey_controller.get_survey_by_short_name")
    def test_case_access_returns_true_when_authorized(
        self,
        get_survey_by_short_name,
        is_respondent_enrolled,
    ):
        get_survey_by_short_name.return_value = self.survey
        is_respondent_enrolled.return_value = True

        result = case_access(
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
            self.survey_id,
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
            case_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                "different-business-party-id",
                self.survey_short_name,
            )

        self.assertEqual(raised.exception.code, 401)
        get_survey_by_short_name.assert_called_once_with(self.survey_short_name)
        is_respondent_enrolled.assert_not_called()

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    @patch("frontstage.common.authorize_access." "survey_controller.get_survey_by_short_name")
    def test_case_access_rejects_mismatched_collection_exercise(
        self,
        get_survey_by_short_name,
        is_respondent_enrolled,
    ):
        get_survey_by_short_name.return_value = self.survey

        mismatched_collection_exercise = {
            **self.collection_exercise,
            "id": "different-collection-exercise-id",
        }

        with self.assertRaises(Unauthorized) as raised:
            case_access(
                self.case,
                mismatched_collection_exercise,
                self.party_id,
                self.business_party_id,
                self.survey_short_name,
            )

        self.assertEqual(raised.exception.code, 401)
        get_survey_by_short_name.assert_called_once_with(self.survey_short_name)
        is_respondent_enrolled.assert_not_called()

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    @patch("frontstage.common.authorize_access." "survey_controller.get_survey_by_short_name")
    def test_case_access_rejects_mismatched_survey(
        self,
        get_survey_by_short_name,
        is_respondent_enrolled,
    ):
        mismatched_survey = {
            **self.survey,
            "id": "different-survey-id",
        }

        get_survey_by_short_name.return_value = mismatched_survey

        with self.assertRaises(Unauthorized) as raised:
            case_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                self.business_party_id,
                self.survey_short_name,
            )

        self.assertEqual(raised.exception.code, 401)
        get_survey_by_short_name.assert_called_once_with(self.survey_short_name)
        is_respondent_enrolled.assert_not_called()

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    @patch("frontstage.common.authorize_access." "survey_controller.get_survey_by_short_name")
    def test_case_access_rejects_not_enrolled(
        self,
        get_survey_by_short_name,
        is_respondent_enrolled,
    ):
        get_survey_by_short_name.return_value = self.survey
        is_respondent_enrolled.return_value = False

        with self.assertRaises(NoSurveyPermission):
            case_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                self.business_party_id,
                self.survey_short_name,
            )

        is_respondent_enrolled.assert_called_once_with(
            self.party_id,
            self.business_party_id,
            self.survey_id,
        )

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    def test_check_enrollment_allows_enrolled_respondent(
        self,
        is_respondent_enrolled,
    ):
        is_respondent_enrolled.return_value = True

        result = check_enrollment(
            self.business_party_id,
            self.case_id,
            self.party_id,
            self.survey,
        )

        self.assertIsNone(result)
        is_respondent_enrolled.assert_called_once_with(
            self.party_id,
            self.business_party_id,
            self.survey_id,
        )

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    def test_check_enrollment_rejects_respondent_without_enrolment(
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

        is_respondent_enrolled.assert_called_once_with(
            self.party_id,
            self.business_party_id,
            self.survey_id,
        )

    def test_check_seft_allows_matching_business_and_survey(self):
        result = check_seft(
            self.business_party_id,
            self.case["caseGroup"],
            self.survey_id,
        )

        self.assertIsNone(result)

    def test_check_seft_rejects_mismatched_business_party(self):
        different_business_party_id = "different-business-party-id"

        with self.assertLogs(
            "frontstage.common.authorize_access",
            level="ERROR",
        ) as captured_logs:
            with self.assertRaises(BadRequest) as raised:
                check_seft(
                    different_business_party_id,
                    self.case["caseGroup"],
                    self.survey_id,
                )

        self.assertEqual(raised.exception.code, 400)
        self.assertIn(
            (
                f"business_party_id {different_business_party_id} "
                "does not match case_group['partyId'] "
                f"{self.business_party_id}"
            ),
            "\n".join(captured_logs.output),
        )

    def test_check_seft_rejects_mismatched_survey(self):
        different_survey_id = "different-survey-id"

        with self.assertLogs(
            "frontstage.common.authorize_access",
            level="ERROR",
        ) as captured_logs:
            with self.assertRaises(BadRequest) as raised:
                check_seft(
                    self.business_party_id,
                    self.case["caseGroup"],
                    different_survey_id,
                )

        self.assertEqual(raised.exception.code, 400)
        self.assertIn(
            (f"survey_id {different_survey_id} and " f"case_group['surveyId'] {self.survey_id}"),
            "\n".join(captured_logs.output),
        )

    @patch("frontstage.common.authorize_access.abort")
    def test_check_seft_stops_after_business_party_mismatch(
        self,
        abort,
    ):
        abort.side_effect = BadRequest()

        with self.assertRaises(BadRequest):
            check_seft(
                "different-business-party-id",
                self.case["caseGroup"],
                "different-survey-id",
            )

        abort.assert_called_once_with(400)
