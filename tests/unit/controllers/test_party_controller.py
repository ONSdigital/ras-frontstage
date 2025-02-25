import unittest
from collections import namedtuple
from unittest.mock import patch

import requests_mock
import responses
from requests import ConnectionError, Timeout

from config import TestingConfig
from frontstage import app
from frontstage.controllers import party_controller
from frontstage.controllers.party_controller import (
    display_button,
    get_respondent_enrolments_for_started_collex,
    get_survey_list_details_for_party,
)
from frontstage.exceptions.exceptions import ApiError, ServiceUnavailableException
from tests.integration.mocked_services import (
    business_party,
    case,
    collection_exercise,
    collection_exercises_for_survey_ids,
    respondent_enrolments,
    respondent_party,
    url_get_business_party,
    url_get_collection_exercises_by_surveys,
    url_get_respondent_email,
    url_get_respondent_enrolments,
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

RESPONDENT_ID = "f956e8ae-6e0f-4414-b0cf-a07c1aa3e37b"
BUSINESS_ID = "252ffe73-8c97-4ef5-899e-3df092454d31"
SURVEY_ID = "f82bf312-d677-484b-be57-c83148446095"
IS_RESPONDENT_ENROLLED_URL = (
    f"{app.config['PARTY_URL']}/party-api/v1/enrolments/is_respondent_enrolled/{RESPONDENT_ID}"
    f"/business_id/{BUSINESS_ID}/survey_id/{SURVEY_ID}"
)


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

    @requests_mock.Mocker()
    def test_get_respondent_enrolments(self, request_mock):
        request_mock.get(url_get_respondent_enrolments, json=respondent_enrolments)
        with app.app_context():
            party = party_controller.get_respondent_enrolments(RESPONDENT_ID)
            self.assertEqual(respondent_enrolments, party)

    @requests_mock.Mocker()
    def test_get_respondent_enrolments_404(self, request_mock):
        request_mock.get(url_get_respondent_enrolments, status_code=404)
        with app.app_context():
            with self.assertRaises(ApiError):
                party_controller.get_respondent_enrolments(RESPONDENT_ID)

    @requests_mock.Mocker()
    def test_get_respondent_enrolments_400(self, request_mock):
        request_mock.get(url_get_respondent_enrolments, status_code=400)
        with app.app_context():
            with self.assertRaises(ApiError):
                party_controller.get_respondent_enrolments(RESPONDENT_ID)

    @requests_mock.Mocker()
    def test_get_respondent_enrolments_ConnectionError(self, request_mock):
        request_mock.get(url_get_respondent_enrolments, exc=ConnectionError)

        with app.app_context():
            with self.assertRaises(ServiceUnavailableException) as exception:
                party_controller.get_respondent_enrolments(RESPONDENT_ID)
        self.assertEqual(["Party service returned a connection error"], exception.exception.errors)

    @requests_mock.Mocker()
    def test_get_respondent_enrolments_timeout(self, request_mock):
        request_mock.get(url_get_respondent_enrolments, exc=Timeout)

        with app.app_context():
            with self.assertRaises(ServiceUnavailableException) as exception:
                party_controller.get_respondent_enrolments(RESPONDENT_ID)
        self.assertEqual(["Party service has timed out"], exception.exception.errors)

    @requests_mock.Mocker()
    def test_is_respondent_enrolled(self, request_mock):
        request_mock.get(IS_RESPONDENT_ENROLLED_URL, json={"enrolled": True})
        with app.app_context():
            is_respondent_enrolled = party_controller.is_respondent_enrolled(RESPONDENT_ID, BUSINESS_ID, SURVEY_ID)
            self.assertTrue(is_respondent_enrolled)

    @requests_mock.Mocker()
    def test_is_respondent_enrolled_400(self, request_mock):
        request_mock.get(IS_RESPONDENT_ENROLLED_URL, status_code=400)
        with app.app_context():
            with self.assertRaises(ApiError):
                party_controller.is_respondent_enrolled(RESPONDENT_ID, BUSINESS_ID, SURVEY_ID)

    @requests_mock.Mocker()
    def test_is_respondent_enrolled_ConnectionError(self, request_mock):
        request_mock.get(IS_RESPONDENT_ENROLLED_URL, exc=ConnectionError)

        with app.app_context():
            with self.assertRaises(ServiceUnavailableException) as exception:
                party_controller.is_respondent_enrolled(RESPONDENT_ID, BUSINESS_ID, SURVEY_ID)
        self.assertEqual(["Party service returned a connection error"], exception.exception.errors)

    @requests_mock.Mocker()
    def test_is_respondent_enrolled_timeout(self, request_mock):
        request_mock.get(IS_RESPONDENT_ENROLLED_URL, exc=Timeout)

        with app.app_context():
            with self.assertRaises(ServiceUnavailableException) as exception:
                party_controller.is_respondent_enrolled(RESPONDENT_ID, BUSINESS_ID, SURVEY_ID)
        self.assertEqual(["Party service has timed out"], exception.exception.errors)

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
            {"survey_details": {"id": "survey1"}},
            {"survey_details": {"id": "survey2"}},
            {"survey_details": {"id": "survey3"}},
        ]

        result = get_respondent_enrolments_for_started_collex(enrolment_data, collex)
        self.assertEqual(len(result), 2)
        self.assertDictEqual({"survey_details": {"id": "survey1"}}, result[0])
        self.assertDictEqual({"survey_details": {"id": "survey3"}}, result[1])

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
    def test_get_survey_list_details_for_party_todo(self, get_collection_instrument):
        # Given party, collection instrument, collection exercise (lower down) and case (lower down) are mocked
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
                "submit_by": "09 Feb 2018",
                "formatted_submit_by": "9th February 2018",
                "due_in": None,
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
                "submit_by": "09 Feb 2018",
                "formatted_submit_by": "9th February 2018",
                "due_in": None,
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
                "submit_by": "09 Feb 2018",
                "formatted_submit_by": "9th February 2018",
                "due_in": None,
                "collection_exercise_ref": "1912",
                "collection_exercise_id": "09286c27-7bba-4b94-8ec1-248c60711ebc",
                "added_survey": None,
                "display_button": True,
            },
        ]
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET, url_get_collection_exercises_by_surveys, json=collection_exercises_for_survey_ids, status=200
            )
            with app.app_context():  # the 2 patches are inside the context to capture the args
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

    @patch("frontstage.controllers.party_controller.RedisCache.get_collection_instrument")
    def test_get_survey_list_details_for_party_without_enrolments(self, get_collection_instrument):
        # Given party, collection instrument and case (lower down) are mocked
        get_collection_instrument.side_effect = [{"type": "SEFT"}, {"type": "EQ"}, {"type": "EQ"}, {"type": "EQ"}]

        expected_response = []

        with responses.RequestsMock() as rsps:
            rsps.add(rsps.GET, url_get_collection_exercises_by_surveys, status=204)
            with app.app_context():  # the 2 patches are inside the context to capture the args
                with patch(
                    "frontstage.controllers.case_controller.get_cases_for_list_type_by_party_id",
                    _get_case_return_value_by_business_id,
                ):
                    # when get_survey_list_details_for_party is called
                    survey_list_details_for_party = get_survey_list_details_for_party(
                        [],
                        "todo",
                        None,
                        None,
                    )

                    # Then the correct list is returned
                    self.assertEqual(list(survey_list_details_for_party), expected_response)

    @staticmethod
    def enrolment_data():
        return [
            {
                "business_details": {
                    "id": "bebee450-46da-4f8b-a7a6-d4632087f2a3",
                    "name": "Test Business 1",
                    "ref": "49910000014",
                    "trading_as": "Trading as Test Business 1",
                },
                "survey_details": {
                    "id": "41320b22-b425-4fba-a90e-718898f718ce",
                    "short_name": "AIFDI",
                    "long_name": "Annual Inward Foreign Direct Investment Survey",
                    "ref": "062",
                },
                "enrolment_status": "ENABLED",
            },
            {
                "business_details": {
                    "id": "fd4d0444-d40a-4c47-996a-de6f5f20658b",
                    "name": "Test Business 2",
                    "ref": "49900000005",
                    "trading_as": "Trading as Test Business 2",
                },
                "survey_details": {
                    "id": "02b9c366-7397-42f7-942a-76dc5876d86d",
                    "short_name": "QBS",
                    "long_name": "Quarterly Business Survey",
                    "ref": "139",
                },
                "enrolment_status": "ENABLED",
            },
            {
                "business_details": {
                    "id": "3ab241f7-b5cc-4cab-a7e6-b6ad6283cbe1",
                    "name": "Test Business 3",
                    "ref": "49900000004",
                    "trading_as": "Trading as Test Business 3",
                },
                "survey_details": {
                    "id": "02b9c366-7397-42f7-942a-76dc5876d86d",
                    "short_name": "QBS",
                    "long_name": "Quarterly Business Survey",
                    "ref": "139",
                },
                "enrolment_status": "ENABLED",
            },
            {
                "business_details": {
                    "id": "4865ad73-684e-4c2c-ba00-aece24f1f27e",
                    "name": "Test Business 4",
                    "ref": "49900000001",
                    "trading_as": "Trading as Test Business 4",
                },
                "survey_details": {
                    "id": "02b9c366-7397-42f7-942a-76dc5876d86d",
                    "short_name": "QBS",
                    "long_name": "Quarterly Business Survey",
                    "ref": "139",
                },
                "enrolment_status": "ENABLED",
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
