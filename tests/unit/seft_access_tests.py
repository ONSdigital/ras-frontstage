import unittest
from unittest.mock import patch

from werkzeug.exceptions import BadRequest

from frontstage.case_access import CaseAccess
from frontstage.exceptions.exceptions import NoSurveyPermission


class SeftAccessTests(unittest.TestCase):

    def setUp(self):
        self.case_access = CaseAccess()

        self.party_id = "respondent-id"
        self.case_id = "case-id"
        self.business_party_id = "business-party-id"

        self.survey = {
            "id": "survey-id",
            "shortName": "QBS",
        }

        self.case_group = {
            "partyId": "business-party-id",
            "surveyId": "survey-id",
        }

    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    def test_check_enrollment_success(
        self,
        is_respondent_enrolled,
    ):
        is_respondent_enrolled.return_value = True

        result = self.case_access.check_enrollment(
            self.business_party_id,
            self.case_id,
            self.party_id,
            self.survey,
        )

        self.assertIsNone(result)

        is_respondent_enrolled.assert_called_once_with(
            self.party_id,
            self.business_party_id,
            self.survey["id"],
        )

    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    def test_check_enrollment_not_enrolled(
        self,
        is_respondent_enrolled,
    ):
        is_respondent_enrolled.return_value = False

        with self.assertRaises(NoSurveyPermission):
            self.case_access.check_enrollment(
                self.business_party_id,
                self.case_id,
                self.party_id,
                self.survey,
            )

        is_respondent_enrolled.assert_called_once_with(
            self.party_id,
            self.business_party_id,
            self.survey["id"],
        )

    def test_check_this_success(self):
        result = self.case_access.check_seft(
            self.business_party_id,
            self.case_group,
            self.survey["id"],
        )

        self.assertIsNone(result)

    def test_check_this_business_party_mismatch(self):
        with self.assertRaises(BadRequest):
            self.case_access.check_seft(
                "different-business-party-id",
                self.case_group,
                self.survey["id"],
            )

    def test_check_this_survey_mismatch(self):
        with self.assertRaises(BadRequest):
            self.case_access.check_seft(
                self.business_party_id,
                self.case_group,
                "different-survey-id",
            )
