import unittest
from unittest.mock import patch

from frontstage.common.authorize_access import check_enrollment
from frontstage.exceptions.exceptions import NoSurveyPermission


class TestValidateEnrollment(unittest.TestCase):

    def setUp(self):

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
            self.survey["id"],
        )

    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    def test_check_enrollment_not_enrolled(
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
            self.survey["id"],
        )
