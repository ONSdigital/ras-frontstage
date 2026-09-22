import unittest
from copy import deepcopy
from unittest.mock import patch

from config import TestingConfig
from frontstage import app
from frontstage.controllers import case_controller
from frontstage.exceptions.exceptions import NoSurveyPermission
from tests.integration.mocked_services import (
    business_party,
    case,
    collection_exercise,
    eq_payload,
    respondent_party,
    survey_eq,
)


class TestCaseAuthorization(unittest.TestCase):
    def setUp(self):
        app.config.from_object(TestingConfig())

        self.case = deepcopy(case)
        self.collection_exercise = deepcopy(collection_exercise)
        self.survey = deepcopy(survey_eq)

        self.case["caseGroup"]["partyId"] = business_party["id"]
        self.case["caseGroup"]["collectionExerciseId"] = self.collection_exercise["id"]
        self.collection_exercise["surveyId"] = self.survey["id"]

    @patch("frontstage.controllers.survey_controller.get_survey_by_short_name")
    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    def test_authorize_case_access_success(self, is_respondent_enrolled, get_survey_by_short_name):
        get_survey_by_short_name.return_value = self.survey
        is_respondent_enrolled.return_value = True

        with app.app_context():
            authorized_business_party_id, authorized_survey = case_controller.authorize_case_access(
                self.case,
                self.collection_exercise,
                respondent_party["id"],
                business_party["id"],
                self.survey["shortName"],
            )

        self.assertEqual(business_party["id"], authorized_business_party_id)
        self.assertEqual(self.survey, authorized_survey)
        get_survey_by_short_name.assert_called_once_with(self.survey["shortName"])
        is_respondent_enrolled.assert_called_once_with(respondent_party["id"], business_party["id"], self.survey["id"])

    @patch("frontstage.controllers.survey_controller.get_survey_by_short_name")
    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    def test_authorize_case_access_rejects_mismatched_business(self, is_respondent_enrolled, get_survey_by_short_name):
        with app.app_context():
            with self.assertRaises(NoSurveyPermission):
                case_controller.authorize_case_access(
                    self.case,
                    self.collection_exercise,
                    respondent_party["id"],
                    "different-business-party-id",
                    self.survey["shortName"],
                )

        get_survey_by_short_name.assert_not_called()
        is_respondent_enrolled.assert_not_called()

    @patch("frontstage.controllers.survey_controller.get_survey_by_short_name")
    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    def test_authorize_case_access_rejects_mismatched_collection_exercise(
        self, is_respondent_enrolled, get_survey_by_short_name
    ):
        self.collection_exercise["id"] = "different-collection-exercise-id"

        with app.app_context():
            with self.assertRaises(NoSurveyPermission):
                case_controller.authorize_case_access(
                    self.case,
                    self.collection_exercise,
                    respondent_party["id"],
                    business_party["id"],
                    self.survey["shortName"],
                )

        get_survey_by_short_name.assert_not_called()
        is_respondent_enrolled.assert_not_called()

    @patch("frontstage.controllers.survey_controller.get_survey_by_short_name")
    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    def test_authorize_case_access_rejects_mismatched_survey(self, is_respondent_enrolled, get_survey_by_short_name):
        different_survey = deepcopy(self.survey)
        different_survey["id"] = "different-survey-id"
        get_survey_by_short_name.return_value = different_survey

        with app.app_context():
            with self.assertRaises(NoSurveyPermission):
                case_controller.authorize_case_access(
                    self.case,
                    self.collection_exercise,
                    respondent_party["id"],
                    business_party["id"],
                    different_survey["shortName"],
                )

        is_respondent_enrolled.assert_not_called()

    @patch("frontstage.controllers.survey_controller.get_survey_by_short_name")
    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    def test_authorize_case_access_rejects_missing_enrolment(self, is_respondent_enrolled, get_survey_by_short_name):
        get_survey_by_short_name.return_value = self.survey
        is_respondent_enrolled.return_value = False

        with app.app_context():
            with self.assertRaises(NoSurveyPermission):
                case_controller.authorize_case_access(
                    self.case,
                    self.collection_exercise,
                    respondent_party["id"],
                    business_party["id"],
                    self.survey["shortName"],
                )

        is_respondent_enrolled.assert_called_once_with(respondent_party["id"], business_party["id"], self.survey["id"])

    @patch("frontstage.controllers.case_controller.post_case_event")
    @patch("frontstage.common.eq_payload.EqPayload.create_payload")
    @patch("frontstage.controllers.case_controller.authorize_case_access")
    def test_get_eq_url_has_no_side_effects_when_authorization_fails(
        self, authorize_case_access, create_payload, post_case_event
    ):
        authorize_case_access.side_effect = NoSurveyPermission(respondent_party["id"], self.case["id"])

        with app.app_context():
            with self.assertRaises(NoSurveyPermission):
                case_controller.get_eq_url(
                    self.case,
                    self.collection_exercise,
                    respondent_party["id"],
                    business_party["id"],
                    self.survey["shortName"],
                )

        create_payload.assert_not_called()
        post_case_event.assert_not_called()

    @patch("frontstage.controllers.case_controller.Encrypter")
    @patch("frontstage.controllers.case_controller.post_case_event")
    @patch("frontstage.common.eq_payload.EqPayload.create_payload")
    @patch("frontstage.controllers.case_controller.authorize_case_access")
    def test_get_eq_url_uses_authorized_business_for_payload(
        self,
        authorize_case_access,
        create_payload,
        post_case_event,
        encrypter,
    ):
        authorize_case_access.return_value = (business_party["id"], self.survey)
        create_payload.return_value = eq_payload
        encrypter.return_value.encrypt.return_value = "encrypted-token"

        with app.app_context():
            eq_url = case_controller.get_eq_url(
                self.case,
                self.collection_exercise,
                respondent_party["id"],
                business_party["id"],
                self.survey["shortName"],
            )

        self.assertEqual(f"{app.config['EQ_V3_URL']}encrypted-token", eq_url)
        create_payload.assert_called_once_with(
            self.case,
            self.collection_exercise,
            respondent_party["id"],
            business_party["id"],
            self.survey,
        )
        post_case_event.assert_called_once_with(
            self.case["id"],
            party_id=respondent_party["id"],
            category="EQ_LAUNCH",
            description=(
                f"Instrument {self.case['collectionInstrumentId']} launched by "
                f"{respondent_party['id']} for case {self.case['id']}"
            ),
        )
