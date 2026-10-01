import unittest
from unittest.mock import patch

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
    def test_authorize_access_returns_true_when_authorized(
        self,
        is_respondent_enrolled,
    ):
        is_respondent_enrolled.return_value = True

        result = authorize_access(
            self.case,
            self.collection_exercise,
            self.party_id,
            self.business_party_id,
            self.survey_id,
        )

        self.assertTrue(result)

        is_respondent_enrolled.assert_called_once_with(
            self.party_id,
            self.business_party_id,
            self.survey_id,
        )

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    def test_authorize_access_rejects_mismatched_business_party(
        self,
        is_respondent_enrolled,
    ):

        with self.assertRaises(NoSurveyPermission) as raised:
            authorize_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                "different-business-party-id",
                self.survey_id,
            )

        self.assertEqual(raised.exception.party_id, self.party_id)
        self.assertEqual(raised.exception.case_id, self.case_id)
        is_respondent_enrolled.assert_not_called()

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    def test_authorize_access_rejects_mismatched_survey(
        self,
        is_respondent_enrolled,
    ):

        with self.assertRaises(NoSurveyPermission) as raised:
            authorize_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                self.business_party_id,
                "wrong-survey-id",
            )

        self.assertEqual(raised.exception.party_id, self.party_id)
        self.assertEqual(raised.exception.case_id, self.case_id)

        is_respondent_enrolled.assert_not_called()

    @patch("frontstage.common.authorize_access." "party_controller.is_respondent_enrolled")
    def test_authorize_access_rejects_not_enrolled(
        self,
        is_respondent_enrolled,
    ):
        is_respondent_enrolled.return_value = False

        with self.assertRaises(NoSurveyPermission):
            authorize_access(
                self.case,
                self.collection_exercise,
                self.party_id,
                self.business_party_id,
                self.survey_id,
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
            self.survey_id,
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
                self.survey_id,
            )

        is_respondent_enrolled.assert_called_once_with(
            self.party_id,
            self.business_party_id,
            self.survey_id,
        )
