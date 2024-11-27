import unittest
from collections import namedtuple
from unittest.mock import patch

import responses

from config import TestingConfig
from frontstage import app
from frontstage.controllers import party_controller
from frontstage.controllers.party_controller import (
    display_button,
    get_respondent_enrolments_for_started_collex,
    get_survey_list_details_for_party,
)
from frontstage.exceptions.exceptions import ApiError
from tests.integration.mocked_services import (
    business_party,
    case,
    collection_exercise,
    respondent_party,
    url_get_business_party,
    url_get_respondent_email,
    url_get_respondent_party,
    url_notify_party_and_respondent_account_locked,
    url_post_add_survey,
    url_reset_password_request,
)

registration_data = {
    "emailAddress": respondent_party["emailAddress"],
    "firstName": respondent_party["firstName"],
    "lastName": respondent_party["lastName"],
    "password": "apples",
    "telephone": respondent_party["telephone"],
    "enrolmentCode": case["iac"],
    "status": "CREATED",
}


class TestPartyController(unittest.TestCase):
    def setUp(self):
        app_config = TestingConfig()
        app.config.from_object(app_config)
        self.app = app.test_client()
        self.app_config = self.app.application.config

    def test_get_respondent_by_party_id_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_respondent_party, json=respondent_party, status=200)

            with app.app_context():
                party = party_controller.get_respondent_party_by_id(respondent_party["id"])

                self.assertEqual(party["id"], respondent_party["id"])
                self.assertEqual(party["emailAddress"], respondent_party["emailAddress"])

    def test_get_respondent_by_party_id_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_respondent_party, status=500)
            with app.app_context():
                with self.assertRaises(ApiError):
                    party_controller.get_respondent_party_by_id(respondent_party["id"])

    def test_get_respondent_by_party_id_not_found(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_respondent_party, status=404)
            with app.app_context():
                party = party_controller.get_respondent_party_by_id(respondent_party["id"])

                self.assertTrue(party is None)

    def test_add_survey_success(self):
        with responses.RequestsMock() as rsps:
            request_json = {"party_id": respondent_party["id"], "enrolment_code": case["iac"]}

            rsps.add(rsps.POST, url_post_add_survey, json=request_json, status=200)
            with app.app_context():
                try:
                    party_controller.add_survey(respondent_party["id"], case["iac"])
                except ApiError:
                    self.fail("Unexpected ApiError when adding a survey")

    def test_add_survey_fail(self):
        with responses.RequestsMock() as rsps:
            request_json = {"party_id": respondent_party["id"], "enrolment_code": case["iac"]}

            rsps.add(rsps.POST, url_post_add_survey, json=request_json, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    party_controller.add_survey(respondent_party["id"], case["iac"])

    def test_get_party_by_business_id_success_without_collection_exercise_id(self):
        """Tests the function is successful when we only supply the mandatory party_id"""
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_business_party, json=business_party, status=200)
            with app.app_context():
                business = party_controller.get_party_by_business_id(
                    business_party["id"], self.app_config["PARTY_URL"], self.app_config["BASIC_AUTH"]
                )

                self.assertEqual(business["id"], business_party["id"])
                self.assertEqual(business["name"], business_party["name"])

    def test_get_party_by_business_id_success_with_collection_exercise_id(self):
        """Tests the function is successful when we supply the optional collection_excercise_id"""
        with responses.RequestsMock() as rsps:
            url = f"{url_get_business_party}?collection_exercise_id={collection_exercise['id']}&verbose=True"
            rsps.add(rsps.GET, url, json=business_party, status=200)
            with app.app_context():
                business = party_controller.get_party_by_business_id(
                    business_party["id"],
                    self.app_config["PARTY_URL"],
                    self.app_config["BASIC_AUTH"],
                    collection_exercise["id"],
                )
                self.assertEqual(business["id"], business_party["id"])
                self.assertEqual(business["name"], business_party["name"])

    def test_get_party_by_business_id_success_with_collection_exercise_id_non_verbose(self):
        """Tests the function calls the expected url when we turn verbose off"""
        called_url = (
            "http://localhost:8081/party-api/v1/businesses/id/be3483c3-f5c9-4b13-bdd7-244db78ff687"
            "?collection_exercise_id=8d990a74-5f07-4765-ac66-df7e1a96505b"
        )

        with responses.RequestsMock() as rsps:
            url = f"{url_get_business_party}?collection_exercise_id={collection_exercise['id']}"
            rsps.add(rsps.GET, url, json=business_party, status=200)
            with app.app_context():
                business = party_controller.get_party_by_business_id(
                    business_party["id"],
                    self.app_config["PARTY_URL"],
                    self.app_config["BASIC_AUTH"],
                    collection_exercise["id"],
                    verbose=False,
                )
                self.assertEqual(business["id"], business_party["id"])
                self.assertEqual(business["name"], business_party["name"])
                self.assertEqual(len(rsps.calls), 1)
                self.assertEqual(rsps.calls[0].request.url, called_url)

    def test_get_party_by_business_id_fail(self):
        called_url = (
            "http://localhost:8081/party-api/v1/businesses/id/be3483c3-f5c9-4b13-bdd7-244db78ff687?verbose=True"
        )
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_business_party, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    party_controller.get_party_by_business_id(
                        business_party["id"], self.app_config["PARTY_URL"], self.app_config["BASIC_AUTH"]
                    )
                self.assertEqual(len(rsps.calls), 1)
                self.assertEqual(rsps.calls[0].request.url, called_url)

    def test_get_respondent_by_email_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_respondent_email, json=respondent_party, status=200)
            with app.app_context():
                respondent = party_controller.get_respondent_by_email(respondent_party["emailAddress"])

                self.assertEqual(respondent["emailAddress"], respondent_party["emailAddress"])
                self.assertEqual(respondent["firstName"], respondent_party["firstName"])

    def test_get_respondent_by_email_not_found(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_respondent_email, status=404)
            with app.app_context():
                respondent = party_controller.get_respondent_by_email(respondent_party["emailAddress"])

                self.assertTrue(respondent is None)

    def test_get_respondent_by_email_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_respondent_email, status=500)
            with app.app_context():
                with self.assertRaises(ApiError):
                    party_controller.get_respondent_by_email(respondent_party["emailAddress"])

    def test_reset_password_request_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.POST, url_reset_password_request, status=500)
            with app.app_context():
                with self.assertRaises(ApiError):
                    party_controller.reset_password_request(respondent_party["emailAddress"])

    def test_lock_respondent_account_success(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.PUT, url_notify_party_and_respondent_account_locked, status=200)
            with app.app_context():
                try:
                    party_controller.notify_party_and_respondent_account_locked(
                        respondent_party["id"], respondent_party["emailAddress"], status="ACTIVE"
                    )
                except ApiError:
                    self.fail("Change respondent status fail to PUT your request")

    def test_lock_respondent_account_fail(self):
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.PUT, url_notify_party_and_respondent_account_locked, status=400)
            with app.app_context():
                with self.assertRaises(ApiError):
                    party_controller.notify_party_and_respondent_account_locked(
                        respondent_party["id"], respondent_party["emailAddress"], status="ACTIVE"
                    )

    def test_get_respondent_enrolments_for_started_collex(self):
        """test that get_respondent_enrolments_for_started_collex will only return enrolment data
        if we have a corresponding collex"""

        collex = {"survey1": "collex1", "survey3": "collex3"}

        enrolment_data = [
            {"survey_id": "survey1", "enrolment_data": "enrolment1"},
            {"survey_id": "survey2", "enrolment_data": "enrolment2"},
            {"survey_id": "survey3", "enrolment_data": "enrolment3"},
        ]

        result = get_respondent_enrolments_for_started_collex(enrolment_data, collex)
        self.assertEqual(len(result), 2)
        self.assertDictEqual({"survey_id": "survey1", "enrolment_data": "enrolment1"}, result[0])
        self.assertDictEqual({"survey_id": "survey3", "enrolment_data": "enrolment3"}, result[1])

    def test_display_button(self):
        Combination = namedtuple("Combination", ["status", "ci_type", "expected"])
        combinations = [
            Combination("COMPLETE", "SEFT", True),
            Combination("COMPLETEDBYPHONE", "SEFT", True),
            Combination("NOLONGERREQUIRED", "SEFT", True),
            Combination("NOTSTARTED", "SEFT", True),
            Combination("INPROGRESS", "SEFT", True),
            Combination("REOPENED", "SEFT", True),
            Combination("REOPENED", "EQ", True),
            Combination("INPROGRESS", "EQ", True),
            Combination("NOTSTARTED", "EQ", True),
            Combination("NOLONGERREQUIRED", "EQ", False),
            Combination("COMPLETEDBYPHONE", "EQ", False),
            Combination("COMPLETE", "EQ", False),
        ]
        for combination in combinations:
            self.assertEqual(display_button(combination.status, combination.ci_type), combination.expected)

    @patch("frontstage.controllers.party_controller.RedisCache.get_collection_instrument")
    @patch("frontstage.controllers.party_controller.RedisCache.get_survey")
    @patch("frontstage.controllers.party_controller.RedisCache.get_business_party")
    def test_get_survey_list_details_for_party_todo(self, get_business_party, get_survey, get_collection_instrument):
        # Given party, survey, collection instrument, collection exercise (lower down) and case (lower down) are mocked
        get_business_party.side_effect = self._business_details_side_effect()
        get_survey.side_effect = self._survey_details_side_effect()
        get_collection_instrument.side_effect = [{"type": "SEFT"}, {"type": "EQ"}, {"type": "EQ"}, {"type": "EQ"}]

        expected_response = [
            {
                "case_id": "e05e3cd3-6707-4751-befa-aaa29481a626",
                "status": "Downloaded",
                "collection_instrument_type": "SEFT",
                "survey_id": "41320b22-b425-4fba-a90e-718898f718ce",
                "survey_long_name": "Annual Inward Foreign Direct Investment Survey",
                "survey_short_name": "AIFDI",
                "survey_ref": "062",
                "business_party_id": "bebee450-46da-4f8b-a7a6-d4632087f2a3",
                "business_name": "Test Business 1",
                "trading_as": "Trading as Test Business 1",
                "business_ref": "49910000014",
                "period": "3001",
                "submit_by": "01 Jan 2030",
                "formatted_submit_by": "1st January 2030",
                "due_in": "Due in over 3 months",
                "collection_exercise_ref": "3001",
                "collection_exercise_id": "6bea2aa8-53a9-4d68-8160-8cbbabfe2d20",
                "added_survey": None,
                "display_button": True,
            },
            {
                "case_id": "000d3115-2e95-4033-8307-0daa8b0a3123",
                "status": "Not started",
                "collection_instrument_type": "EQ",
                "survey_id": "02b9c366-7397-42f7-942a-76dc5876d86d",
                "survey_long_name": "Quarterly Business Survey",
                "survey_short_name": "QBS",
                "survey_ref": "139",
                "business_party_id": "fd4d0444-d40a-4c47-996a-de6f5f20658b",
                "business_name": "Test Business 2",
                "trading_as": "Trading as Test Business 2",
                "business_ref": "49900000005",
                "period": "December",
                "submit_by": "29 Nov 2024",
                "formatted_submit_by": "29th November 2024",
                "due_in": "Due in 3 days",
                "collection_exercise_ref": "1912",
                "collection_exercise_id": "09286c27-7bba-4b94-8ec1-248c60711ebc",
                "added_survey": None,
                "display_button": True,
            },
            {
                "case_id": "e11d8652-bd92-46ca-a984-a586966c7c16",
                "status": "In progress",
                "collection_instrument_type": "EQ",
                "survey_id": "02b9c366-7397-42f7-942a-76dc5876d86d",
                "survey_long_name": "Quarterly Business Survey",
                "survey_short_name": "QBS",
                "survey_ref": "139",
                "business_party_id": "3ab241f7-b5cc-4cab-a7e6-b6ad6283cbe1",
                "business_name": "Test Business 3",
                "trading_as": "Trading as Test Business 3",
                "business_ref": "49900000004",
                "period": "December",
                "submit_by": "29 Nov 2024",
                "formatted_submit_by": "29th November 2024",
                "due_in": "Due in 3 days",
                "collection_exercise_ref": "1912",
                "collection_exercise_id": "09286c27-7bba-4b94-8ec1-248c60711ebc",
                "added_survey": None,
                "display_button": True,
            },
        ]

        with app.app_context():  # the 2 patches are inside the context to capture the args
            with patch(
                "frontstage.controllers.party_controller.RedisCache.get_collection_exercises_by_survey",
                _get_ces_return_value_by_survey_id,
            ):
                with patch(
                    "frontstage.controllers.case_controller.get_cases_for_list_type_by_party_id",
                    _get_case_return_value_by_business_id,
                ):
                    # when get_survey_list_details_for_party is called
                    survey_list_details_for_party = get_survey_list_details_for_party(
                        self.enrolment_data(), "todo", None, None
                    )

                    # Then the correct list is returned
                    self.assertEqual(list(survey_list_details_for_party), expected_response)

    @staticmethod
    def enrolment_data():
        return [
            {
                "business_id": "bebee450-46da-4f8b-a7a6-d4632087f2a3",
                "survey_id": "41320b22-b425-4fba-a90e-718898f718ce",
                "status": "ENABLED",
            },
            {
                "business_id": "fd4d0444-d40a-4c47-996a-de6f5f20658b",
                "survey_id": "02b9c366-7397-42f7-942a-76dc5876d86d",
                "status": "ENABLED",
            },
            {
                "business_id": "3ab241f7-b5cc-4cab-a7e6-b6ad6283cbe1",
                "survey_id": "02b9c366-7397-42f7-942a-76dc5876d86d",
                "status": "ENABLED",
            },
            {
                "business_id": "4865ad73-684e-4c2c-ba00-aece24f1f27e",
                "survey_id": "02b9c366-7397-42f7-942a-76dc5876d86d",
                "status": "ENABLED",
            },
        ]

    @staticmethod
    def _survey_details_side_effect():
        # This isn't a mistake the code calls out to QBS 3 times, but Redis prevents 3 calls to the service.
        return [
            {
                "id": "41320b22-b425-4fba-a90e-718898f718ce",
                "shortName": "AIFDI",
                "longName": "Annual Inward Foreign Direct Investment Survey",
                "surveyRef": "062",
                "surveyMode": "SEFT",
            },
            {
                "id": "02b9c366-7397-42f7-942a-76dc5876d86d",
                "shortName": "QBS",
                "longName": "Quarterly Business Survey",
                "surveyRef": "139",
                "surveyMode": "EQ",
            },
            {
                "id": "02b9c366-7397-42f7-942a-76dc5876d86d",
                "shortName": "QBS",
                "longName": "Quarterly Business Survey",
                "surveyRef": "139",
                "surveyMode": "EQ",
            },
            {
                "id": "02b9c366-7397-42f7-942a-76dc5876d86d",
                "shortName": "QBS",
                "longName": "Quarterly Business Survey",
                "surveyRef": "139",
                "surveyMode": "EQ",
            },
        ]

    @staticmethod
    def _business_details_side_effect():
        return [
            {
                "id": "bebee450-46da-4f8b-a7a6-d4632087f2a3",
                "name": "Test Business 1",
                "sampleUnitRef": "49910000014",
                "trading_as": "Trading as Test Business 1",
            },
            {
                "id": "fd4d0444-d40a-4c47-996a-de6f5f20658b",
                "name": "Test Business 2",
                "sampleUnitRef": "49900000005",
                "trading_as": "Trading as Test Business 2",
            },
            {
                "id": "3ab241f7-b5cc-4cab-a7e6-b6ad6283cbe1",
                "name": "Test Business 3",
                "sampleUnitRef": "49900000004",
                "trading_as": "Trading as Test Business 3",
            },
            {
                "id": "4865ad73-684e-4c2c-ba00-aece24f1f27e",
                "name": "Test Business 4",
                "sampleUnitRef": "49900000001",
                "trading_as": "Trading as Test Business 4",
            },
        ]


def _get_case_return_value_by_business_id(*args):
    """returns the correct case details based on the business_id used in the patched called"""

    business_id = args[0]
    if business_id == "bebee450-46da-4f8b-a7a6-d4632087f2a3":
        return [
            {
                "id": "e05e3cd3-6707-4751-befa-aaa29481a626",
                "collectionInstrumentId": "37cffd1b-b7e2-4ce0-b4d1-1e4f932189e2",
                "partyId": "bebee450-46da-4f8b-a7a6-d4632087f2a3",
                "caseGroup": {
                    "collectionExerciseId": "6bea2aa8-53a9-4d68-8160-8cbbabfe2d20",
                    "caseGroupStatus": "INPROGRESS",
                },
            },
            {
                "id": "6e6b49ae-76ae-458d-9dd2-447bc6ff37de",
                "collectionInstrumentId": "04a1a6f6-fe98-4fea-a2ab-d452d75b2a53",
                "partyId": "bebee450-46da-4f8b-a7a6-d4632087f2a3",
                "caseGroup": {
                    "collectionExerciseId": "398cf4c5-7f3b-4bfe-a8b9-2d51a0b598a4",
                    "caseGroupStatus": "NOTSTARTED",
                },
            },
        ]

    elif business_id == "3ab241f7-b5cc-4cab-a7e6-b6ad6283cbe1":
        return [
            {
                "id": "e11d8652-bd92-46ca-a984-a586966c7c16",
                "collectionInstrumentId": "07b96b43-ab74-40d5-aaac-786c92e5dce2",
                "partyId": "3ab241f7-b5cc-4cab-a7e6-b6ad6283cbe1",
                "caseGroup": {
                    "collectionExerciseId": "09286c27-7bba-4b94-8ec1-248c60711ebc",
                    "caseGroupStatus": "INPROGRESS",
                },
            }
        ]
    elif business_id == "fd4d0444-d40a-4c47-996a-de6f5f20658b":
        return [
            {
                "id": "000d3115-2e95-4033-8307-0daa8b0a3123",
                "collectionInstrumentId": "07b96b43-ab74-40d5-aaac-786c92e5dce2",
                "partyId": "fd4d0444-d40a-4c47-996a-de6f5f20658b",
                "caseGroup": {
                    "collectionExerciseId": "09286c27-7bba-4b94-8ec1-248c60711ebc",
                    "caseGroupStatus": "NOTSTARTED",
                },
            }
        ]
    else:
        return []


def _get_ces_return_value_by_survey_id(*args):
    """returns the correct collection exercise details based on the survey_id used in the patched called"""
    survey_id = args[1]
    if survey_id == "41320b22-b425-4fba-a90e-718898f718ce":
        return [
            {
                "id": "6bea2aa8-53a9-4d68-8160-8cbbabfe2d20",
                "surveyId": "41320b22-b425-4fba-a90e-718898f718ce",
                "exerciseRef": "3001",
                "userDescription": "3001",
                "events": {
                    "return_by": {
                        "date": "01 Jan 2030",
                        "formatted_date": "1st January 2030",
                        "due_time": "Due in over 3 months",
                    }
                },
            }
        ]
    else:
        return [
            {
                "id": "09286c27-7bba-4b94-8ec1-248c60711ebc",
                "surveyId": "02b9c366-7397-42f7-942a-76dc5876d86d",
                "exerciseRef": "1912",
                "userDescription": "December",
                "events": {
                    "return_by": {
                        "date": "29 Nov 2024",
                        "formatted_date": "29th November 2024",
                        "due_time": "Due in 3 days",
                    }
                },
            }
        ]
