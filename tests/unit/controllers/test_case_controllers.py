import unittest
from copy import deepcopy
from unittest.mock import patch

import responses
from werkzeug.exceptions import Forbidden

from config import TestingConfig
from frontstage import app
from frontstage.controllers import case_controller
from frontstage.exceptions.exceptions import (
    ApiError,
    InvalidCaseCategory,
    NoSurveyPermission,
)
from tests.integration.mocked_services import (
    business_party,
    case,
    case_list,
    case_list_with_iac_and_case_events,
    categories,
    collection_exercise,
    collection_instrument_seft,
    eq_payload,
    respondent_party,
    survey,
    survey_eq,
    url_get_case,
    url_get_case_by_enrolment_code,
    url_get_case_categories,
    url_get_cases_by_party,
    url_get_survey_by_short_name,
    url_get_survey_by_short_name_eq,
    url_post_case_event_uuid,
)


class TestCaseControllers(unittest.TestCase):
    def setUp(self):
        app_config = TestingConfig()
        app.config.from_object(app_config)
        self.app = app.test_client()
        self.app_config = self.app.application.config

    def test_calculate_case_status_returns_correct_status_for_complete_for_eq_and_seft(self):

        case_status_seft = case_controller.calculate_case_status("COMPLETE", "SEFT")
        case_status_eq = case_controller.calculate_case_status("COMPLETE", "EQ")

        self.assertEqual("Complete", case_status_seft)
        self.assertEqual("Complete", case_status_eq)

    def test_calculate_case_status_returns_correct_status_for_completed_by_phone_for_eq_and_seft(self):

        case_status_seft = case_controller.calculate_case_status("COMPLETEDBYPHONE", "SEFT")
        case_status_eq = case_controller.calculate_case_status("COMPLETEDBYPHONE", "EQ")

        self.assertEqual("Completed by phone", case_status_seft)
        self.assertEqual("Completed by phone", case_status_eq)

    def test_calculate_case_status_returns_correct_status_for_no_longer_required_for_eq_and_seft(self):

        case_status_seft = case_controller.calculate_case_status("NOLONGERREQUIRED", "SEFT")
        case_status_eq = case_controller.calculate_case_status("NOLONGERREQUIRED", "EQ")

        self.assertEqual("No longer required", case_status_seft)
        self.assertEqual("No longer required", case_status_eq)

    def test_calculate_case_status_returns_correct_state_for_in_progress_for_eq_and_seft(self):

        case_status_seft = case_controller.calculate_case_status("INPROGRESS", "SEFT")
        case_status_eq = case_controller.calculate_case_status("INPROGRESS", "EQ")

        self.assertEqual("Downloaded", case_status_seft)
        self.assertEqual("In progress", case_status_eq)

    def test_calculate_case_status_returns_not_started_with_unexpected_status(self):

        case_status_seft = case_controller.calculate_case_status("Apple", "SEFT")
        case_status_eq = case_controller.calculate_case_status("Banana", "EQ")

        self.assertEqual("Not started", case_status_seft)
        self.assertEqual("Not started", case_status_eq)

    def test_get_case_by_id_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_case, json=case, status=200, content_type="application/json")
            with app.app_context():
                get_case = case_controller.get_case_by_case_id(case["id"])

                self.assertEqual(case["partyId"], get_case["partyId"])

    def test_get_case_by_id_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_case, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    case_controller.get_case_by_case_id(case["id"])

    def test_get_case_by_enrolment_code_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_case_by_enrolment_code, json=case, status=200, content_type="application/json")
            with app.app_context():
                get_case = case_controller.get_case_by_enrolment_code(case["iac"])

                self.assertEqual(get_case["iac"], case["iac"])
                self.assertEqual(get_case["id"], case["id"])

    def test_get_case_by_enrolment_code_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_case_by_enrolment_code, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    case_controller.get_case_by_enrolment_code(case["iac"])

    def test_get_case_categories_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_case_categories, json=categories, status=200, content_type="application/json")
            with app.app_context():
                get_categories = case_controller.get_case_categories()

                self.assertEqual(get_categories[0]["name"], categories[0]["name"])

    def test_get_case_categories_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_case_categories, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    self.assertRaises(ApiError, case_controller.get_case_categories())

    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    @patch("frontstage.controllers.case_controller.post_case_event")
    @patch("frontstage.common.eq_payload.EqPayload.create_payload")
    @patch("frontstage.controllers.case_controller.get_case_by_case_id")
    def test_get_eq_url_case_group_status_not_complete(self, get_case_by_id, create_eq_payload, *_):
        get_case_by_id.return_value = case
        create_eq_payload.return_value = eq_payload
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_survey_by_short_name_eq, json=survey_eq, status=200)
            with app.app_context():
                eq_url = case_controller.get_eq_url(
                    case,
                    collection_exercise,
                    respondent_party["id"],
                    business_party["id"],
                    survey_eq["shortName"],
                )

                self.assertIn("https://eq-test/v3/session?token=", eq_url)

    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    @patch("frontstage.controllers.case_controller.post_case_event")
    @patch("frontstage.common.eq_payload.EqPayload.create_payload")
    @patch("frontstage.controllers.case_controller.get_case_by_case_id")
    def test_get_eq_v3_url_case_group_status_not_complete(self, get_case_by_id, create_eq_payload, *_):
        get_case_by_id.return_value = case
        create_eq_payload.return_value = eq_payload
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_survey_by_short_name_eq, json=survey_eq, status=200)
            with app.app_context():
                eq_url = case_controller.get_eq_url(
                    case,
                    collection_exercise,
                    respondent_party["id"],
                    business_party["id"],
                    survey_eq["shortName"],
                )

                self.assertIn("https://eq-test/v3/session?token=", eq_url)

    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    @patch("frontstage.controllers.case_controller.get_case_by_case_id")
    def test_get_eq_url_when_caseGroupStatus_is_complete(self, get_case_by_id, _):
        case_copy = deepcopy(case)
        case_copy["caseGroup"]["caseGroupStatus"] = "COMPLETE"
        get_case_by_id.return_value = case_copy
        with app.app_context():
            with self.assertRaises(Forbidden):
                case_controller.get_eq_url(
                    case_copy,
                    collection_exercise,
                    respondent_party["id"],
                    business_party["id"],
                    survey_eq["shortName"],
                )

    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    @patch("frontstage.controllers.case_controller.get_case_by_case_id")
    def test_get_eq_url_when_caseGroupStatus_is_completed_by_phone(self, get_case_by_id, _):
        case_copy = deepcopy(case)
        case_copy["caseGroup"]["caseGroupStatus"] = "COMPLETEDBYPHONE"
        get_case_by_id.return_value = case_copy
        with app.app_context():
            with self.assertRaises(Forbidden):
                case_controller.get_eq_url(
                    case_copy,
                    collection_exercise,
                    respondent_party["id"],
                    business_party["id"],
                    survey_eq["shortName"],
                )

    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    @patch("frontstage.controllers.case_controller.get_case_by_case_id")
    def test_get_eq_url_when_caseGroupStatus_is_no_longer_required(self, get_case_by_id, _):
        case_copy = deepcopy(case)
        case_copy["caseGroup"]["caseGroupStatus"] = "NOLONGERREQUIRED"
        get_case_by_id.return_value = case_copy
        with app.app_context():
            with self.assertRaises(Forbidden):
                case_controller.get_eq_url(
                    case_copy,
                    collection_exercise,
                    respondent_party["id"],
                    business_party["id"],
                    survey_eq["shortName"],
                )

    @patch("frontstage.controllers.case_controller.get_case_by_case_id")
    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    def test_get_eq_url_no_survey_permission(self, is_respondent_enrolled, get_case_by_id):
        is_respondent_enrolled.return_value = False
        get_case_by_id.return_value = case

        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_survey_by_short_name_eq, json=survey_eq, status=200)
            with app.app_context():
                with self.assertRaises(NoSurveyPermission):
                    case_controller.get_eq_url(
                        case,
                        collection_exercise,
                        respondent_party["id"],
                        business_party["id"],
                        survey_eq["shortName"],
                    )

    @patch("frontstage.controllers.case_controller.validate_case_category")
    def test_post_case_event_success(self, _):
        message = {
            "description": "Access code authentication attempted'",
            "category": "ACCESS_CODE_AUTHENTICATION_ATTEMPT",
            "partyId": respondent_party["id"],
            "createdBy": "RAS_FRONTSTAGE",
        }
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.POST, url_post_case_event_uuid, json=message, status=200)
            with app.app_context():
                try:
                    case_controller.post_case_event(
                        case["id"], respondent_party["id"], message["category"], message["description"]
                    )
                except ApiError:
                    self.fail("Unexpected ApiError thrown when posting case event")

    @patch("frontstage.controllers.case_controller.validate_case_category")
    def test_post_case_event_fail(self, _):
        message = {
            "description": "Access code authentication attempted'",
            "category": "ACCESS_CODE_AUTHENTICATION_ATTEMPT",
            "partyId": respondent_party["id"],
            "createdBy": "RAS_FRONTSTAGE",
        }
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.POST, url_post_case_event_uuid, json=message, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    case_controller.post_case_event(
                        case["id"], respondent_party["id"], message["category"], message["description"]
                    )

    @patch("frontstage.controllers.case_controller.get_case_categories")
    def test_validate_case_category_valid_category(self, get_case_event_categories):
        get_case_event_categories.return_value = categories

        try:
            case_controller.validate_case_category(categories[0]["name"])
        except InvalidCaseCategory:
            self.fail("Unexpected validation fail for case category")

    @patch("frontstage.controllers.case_controller.get_case_categories")
    def test_validate_case_category_invalid_category(self, get_case_event_categories):
        get_case_event_categories.return_value = categories

        with self.assertRaises(InvalidCaseCategory):
            case_controller.validate_case_category("Banana")

    @patch("frontstage.controllers.case_controller.get_cases_by_party_id")
    def test_get_cases_for_list_type_by_party_id_todo(self, get_cases_by_party_id):
        get_cases_by_party_id.return_value = case_list

        cases = case_controller.get_cases_for_list_type_by_party_id(
            respondent_party["id"], self.app_config["CASE_URL"], self.app_config["BASIC_AUTH"]
        )
        for business_case in cases:
            for status in ["COMPLETE", "COMPLETEDBYPHONE", "NOLONGERREQUIRED"]:
                self.assertNotIn(business_case["caseGroup"]["caseGroupStatus"], status)

    @patch("frontstage.controllers.case_controller.get_cases_by_party_id")
    def test_get_cases_for_list_type_by_party_id_history(self, get_cases_by_party_id):
        get_cases_by_party_id.return_value = case_list

        cases = case_controller.get_cases_for_list_type_by_party_id(
            respondent_party["id"], self.app_config["CASE_URL"], self.app_config["BASIC_AUTH"], list_type="history"
        )

        for business_case in cases:
            for status in ["INPROGRESS", "NOTSTARTED", "REOPENED"]:
                self.assertNotIn(business_case["caseGroup"]["caseGroupStatus"], status)

    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    @patch("frontstage.controllers.case_controller.get_case_by_case_id")
    @patch("frontstage.controllers.party_controller.get_party_by_business_id")
    @patch("frontstage.controllers.survey_controller.get_survey_by_short_name")
    @patch("frontstage.controllers.collection_instrument_controller.get_collection_instrument")
    @patch("frontstage.controllers.collection_exercise_controller.get_collection_exercise")
    def test_get_case_data_success(
        self,
        get_collection_exercise,
        get_collection_instrument,
        get_survey_by_short_name,
        get_party_by_business_id,
        get_case,
        _,
    ):

        get_collection_exercise.return_value = collection_exercise
        get_collection_instrument.return_value = collection_instrument_seft
        get_survey_by_short_name.return_value = survey
        get_party_by_business_id.return_value = business_party
        get_case.return_value = case

        with app.app_context():
            case_data = case_controller.get_case_data(
                case["id"], respondent_party["id"], business_party["id"], survey["shortName"]
            )

            self.assertEqual(collection_exercise["id"], case_data["collection_exercise"]["id"])
            self.assertEqual(collection_instrument_seft["id"], case_data["collection_instrument"]["id"])
            self.assertEqual(survey["shortName"], case_data["survey"]["shortName"])
            self.assertEqual(business_party["id"], case_data["business_party"]["id"])

    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    @patch("frontstage.controllers.case_controller.get_case_by_case_id")
    def test_get_case_data_no_survey_permission(self, get_case_by_id, is_respondent_enrolled):
        get_case_by_id.return_value = case
        is_respondent_enrolled.return_value = False

        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_survey_by_short_name, json=survey, status=200)
            with app.app_context():
                with self.assertRaises(NoSurveyPermission):
                    case_controller.get_case_data(
                        case["id"], respondent_party["id"], business_party["id"], survey["shortName"]
                    )

    def test_get_cases_by_party_id_with_case_events(self):
        with responses.RequestsMock() as rsps:
            url = f"{url_get_cases_by_party}?caseevents=true"
            rsps.add(rsps.GET, url, json=case_list, status=200)
            with app.app_context():
                returned_cases = case_controller.get_cases_by_party_id(
                    case["partyId"], self.app_config["CASE_URL"], self.app_config["BASIC_AUTH"], case_events=True
                )

                self.assertNotEqual(len(returned_cases), 0)

    def test_get_cases_by_party_id_without_case_events(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_cases_by_party, json=case_list, status=200)
            with app.app_context():
                returned_cases = case_controller.get_cases_by_party_id(
                    case["partyId"], self.app_config["CASE_URL"], self.app_config["BASIC_AUTH"]
                )

                self.assertNotEqual(len(returned_cases), 0)

    def test_get_cases_by_party_id_without_iac(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_cases_by_party, json=case_list, status=200)
            with app.app_context():
                returned_cases = case_controller.get_cases_by_party_id(
                    case["partyId"], self.app_config["CASE_URL"], self.app_config["BASIC_AUTH"], iac=False
                )

                self.assertNotEqual(len(returned_cases), 0)
                self.assertIsNone(returned_cases[0]["iac"])

    def test_get_cases_by_party_id_without_iac_and_with_case_events(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_cases_by_party, json=case_list_with_iac_and_case_events, status=200)
            with app.app_context():
                returned_cases = case_controller.get_cases_by_party_id(
                    case["partyId"],
                    self.app_config["CASE_URL"],
                    self.app_config["BASIC_AUTH"],
                    iac=False,
                    case_events=True,
                )

                self.assertNotEqual(len(returned_cases), 0)
                self.assertIsNone(returned_cases[0]["iac"])
                self.assertIsNotNone(returned_cases[0]["caseEvents"][0])

    def test_get_cases_by_party_id_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_cases_by_party, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    case_controller.get_cases_by_party_id(
                        case["partyId"], self.app_config["CASE_URL"], self.app_config["BASIC_AUTH"]
                    )
