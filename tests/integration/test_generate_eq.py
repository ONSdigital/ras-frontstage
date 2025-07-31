import json
import unittest
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch

import requests_mock
from freezegun import freeze_time

from frontstage import app
from frontstage.common.eq_payload import EqPayload
from frontstage.controllers import collection_exercise_controller
from frontstage.exceptions.exceptions import ApiError, InvalidEqPayLoad
from tests.integration.mocked_services import (
    business_party,
    case,
    collection_exercise,
    collection_exercise_events,
    collection_exercise_with_supplementary_dataset,
    collection_instrument_seft,
    respondent_party,
    survey,
    survey_eq,
    url_banner_api,
    url_get_business_party,
    url_get_ci,
    url_get_collection_exercise,
    url_get_collection_exercise_events,
    url_get_survey,
    url_registry_instrument,
)

encoded_jwt_token = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwYXJ0eV9pZCI6ImY5NTZlOGFlLTZ"
    "lMGYtNDQxNC1iMGNmLWEwN2MxYWEzZTM3YiIsImV4cGlyZXNfYXQiOiIxMDAxMjM0NTY"
    "3ODkiLCJyb2xlIjoicmVzcG9uZGVudCIsInVucmVhZF9tZXNzYWdlX2NvdW50Ijp7InZh"
    "bHVlIjowLCJyZWZyZXNoX2luIjozMjUyNzY3NDAwMC4wfSwiZXhwaXJlc19pbiI6MzI1M"
    "jc2NzQwMDAuMH0.m94R50EPIKTJmE6gf6PvCmCq8ZpYwwV8PHSqsJh5fnI"
)

with open("tests/test_data/collection_instrument/collection_instrument_eq.json") as json_data:
    collection_instrument_eq = json.load(json_data)

TIME_TO_FREEZE = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

# Note that the version mentioned here is the RM->EQ communication version, not the EQ version
PAYLOAD = {
    "exp": 1672574700,
    "iat": 1672574400,
    "version": "v2",
    "account_service_url": "http://frontstage-url/surveys",
    "case_id": "8cdc01f9-656a-4715-a148-ffed0dbe1b04",
    "collection_exercise_sid": "8d990a74-5f07-4765-ac66-df7e1a96505b",
    "response_id": "49900000001F8d990a74-5f07-4765-ac66-df7e1a96505b20001",
    "schema_name": "2_0001",
    "survey_metadata": {
        "data": {
            "case_ref": "1000000000000016",
            "form_type": "0001",
            "period_id": "204901",
            "period_str": "test_exercise",
            "ref_p_start_date": "2018-04-10",
            "ref_p_end_date": "2020-05-31",
            "ru_name": "RUNAME1_COMPANY1 RUNNAME2_COMPANY1",
            "ru_ref": "49900000001F",
            "trad_as": "  ",
            "user_id": "f956e8ae-6e0f-4414-b0cf-a07c1aa3e37b",
            "survey_id": "139",
        }
    },
}

with open("tests/test_data/registry_instrument/registry_instrument.json") as fp:
    registry_instrument = json.load(fp)


class TestGenerateEqURL(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie("authorization", "session_key")
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLC"
            "J1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8"
            "Q5U9VVdy54"
            # NOQA
        }
        self.patcher = patch("redis.StrictRedis.get", return_value=encoded_jwt_token)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @freeze_time(TIME_TO_FREEZE)
    @requests_mock.mock()
    def test_create_payload_without_employment_date(self, mock_request):
        # Given a collection exercise without an employment date event
        mock_request.get(url_get_collection_exercise_events, json=collection_exercise_events)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_ci, json=collection_instrument_eq)
        mock_request.get(url_registry_instrument, json=registry_instrument)

        # When a payload is created
        with app.app_context():
            payload_created = EqPayload().create_payload(
                case, collection_exercise, respondent_party["id"], business_party["id"], survey_eq
            )
        # Then the payload is as expected
        self.assertTrue(PAYLOAD.items() <= payload_created.items())
        self.assertIn("jti", payload_created)
        self.assertTrue(_is_valid_uuid(payload_created["jti"]))
        self.assertIn("tx_id", payload_created)
        self.assertTrue(_is_valid_uuid(payload_created["tx_id"]))
        self.assertNotIn("employment_date", payload_created)

    @freeze_time(TIME_TO_FREEZE)
    @requests_mock.mock()
    def test_create_payload_with_employment_date(self, mock_request):
        # Given a collection exercise with an employment date event
        collection_exercise_event_employment_date = {
            "id": "5629d715-ec3e-4ca2-9232-be5c1d56cf32",
            "collectionExerciseId": "df634637-2aac-487f-9d2f-eb56615ed80e",
            "tag": "employment",
            "timestamp": "2023-05-31T00:00:00.000Z",
        }
        collection_exercise_events.append(collection_exercise_event_employment_date)
        PAYLOAD["survey_metadata"]["data"]["employment_date"] = "2023-05-31"
        mock_request.get(url_get_collection_exercise_events, json=collection_exercise_events)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_ci, json=collection_instrument_eq)
        mock_request.get(url_registry_instrument, json=registry_instrument)

        # When a payload is created
        with app.app_context():
            payload_created = EqPayload().create_payload(
                case, collection_exercise, respondent_party["id"], business_party["id"], survey_eq
            )

        # Then the payload is as expected
        self.assertTrue(PAYLOAD.items() <= payload_created.items())
        self.assertTrue("jti" in payload_created)
        self.assertTrue(_is_valid_uuid(payload_created["jti"]))
        self.assertTrue("tx_id" in payload_created)
        self.assertTrue(_is_valid_uuid(payload_created["tx_id"]))

    @requests_mock.mock()
    def test_generate_eq_url_seft(self, mock_request):
        # Given all external services are mocked and we have seft collection instrument
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_events, json=collection_exercise_events)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_seft)
        mock_request.get(url_banner_api, status_code=404)

        # When create_payload is called
        # Then an InvalidEqPayLoad is raised
        with app.app_context():
            with self.assertRaises(InvalidEqPayLoad) as e:
                EqPayload().create_payload(
                    case,
                    collection_exercise,
                    party_id=respondent_party["id"],
                    business_party_id=business_party["id"],
                    survey=survey_eq,
                )
        self.assertEqual(
            e.exception.message, "Collection instrument 68ad4018-2ddd-4894-89e7-33f0135887a2 type is not EQ"
        )

    @requests_mock.mock()
    def test_generate_eq_url_no_eq_id(self, mock_request):
        # Given all external services are mocked and we have an EQ collection instrument without an EQ ID
        with open("tests/test_data/collection_instrument/collection_instrument_eq_no_eq_id.json") as json_data:
            collection_instrument_eq_no_eq_id = json.load(json_data)

        mock_request.get(url_get_ci, json=collection_instrument_eq_no_eq_id)
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_registry_instrument, json=registry_instrument)

        # When create_payload is called
        # Then an InvalidEqPayLoad is raised
        with app.app_context():
            with self.assertRaises(InvalidEqPayLoad) as e:
                EqPayload().create_payload(
                    case,
                    collection_exercise,
                    party_id=respondent_party["id"],
                    business_party_id=business_party["id"],
                    survey=survey_eq,
                )
        self.assertEqual(
            e.exception.message,
            "Collection instrument 68ad4018-2ddd-4894-89e7-33f0135887a2 " "classifiers are incorrect or missing",
        )

    @requests_mock.mock()
    def test_generate_eq_url_contains_response_id(self, mock_request):
        # Given all external services are mocked and we have an EQ collection instrument without an EQ ID
        mock_request.get(url_get_collection_exercise_events, json=collection_exercise_events)
        mock_request.get(url_get_business_party, json=business_party)
        with open("tests/test_data/collection_instrument/collection_instrument_eq.json") as json_data:
            collection_instrument_eq = json.load(json_data)

        mock_request.get(url_get_ci, json=collection_instrument_eq)
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_registry_instrument, json=registry_instrument)

        # When create_payload is called
        # Then an InvalidEqPayLoad is raised
        with app.app_context():
            payload = EqPayload().create_payload(
                case,
                collection_exercise,
                party_id=respondent_party["id"],
                business_party_id=business_party["id"],
                survey=survey_eq,
            )
        self.assertTrue("response_id" in payload)
        self.assertEqual("49900000001F8d990a74-5f07-4765-ac66-df7e1a96505b20001", payload["response_id"])

    @requests_mock.mock()
    def test_generate_eq_url_no_form_type(self, mock_request):
        # Given all external services are mocked and we have an EQ collection instrument without a Form_type
        with open("tests/test_data/collection_instrument/collection_instrument_eq_no_form_type.json") as json_data:
            collection_instrument_eq_no_form_type = json.load(json_data)

        mock_request.get(url_get_ci, json=collection_instrument_eq_no_form_type)
        mock_request.get(url_banner_api, status_code=404)
        mock_request.get(url_registry_instrument, json=None)

        # When create_payload is called
        # Then an InvalidEqPayLoad is raised
        with app.app_context():
            with self.assertRaises(InvalidEqPayLoad) as e:
                EqPayload().create_payload(
                    case,
                    collection_exercise,
                    party_id=respondent_party["id"],
                    business_party_id=business_party["id"],
                    survey=survey_eq,
                )
        self.assertEqual(
            e.exception.message,
            "Collection instrument 68ad4018-2ddd-4894-89e7-33f0135887a2 " "classifiers are incorrect or missing",
        )

    @requests_mock.mock()
    def test_access_collection_exercise_events_fail(self, mock_request):
        # Given a failing collection exercise events service
        mock_request.get(url_get_collection_exercise_events, status_code=500)
        mock_request.get(url_banner_api, status_code=404)

        # When get collection exercise events is called
        # Then an ApiError is raised
        with app.app_context():
            with self.assertRaises(ApiError):
                collection_exercise_controller.get_collection_exercise_events(collection_exercise["id"])

    def test_generate_eq_url_incorrect_date_format(self):
        # Given an invalid date
        date = "invalid"

        # When format_string_long_date_time_to_short_date is called
        # Then an InvalidEqPayLoad is raised
        with self.assertRaises(InvalidEqPayLoad) as e:
            EqPayload()._format_string_long_date_time_to_short_date(date)
        self.assertEqual(e.exception.message, "Unable to format invalid")

    def test_generate_eq_url_iso8601_date_format(self):
        # Given a valid date
        date = "2007-01-25T12:00:00Z"

        # When format_string_long_date_time_to_short_date is called
        # Then the correct date is returned
        result = EqPayload()._format_string_long_date_time_to_short_date(date)
        self.assertEqual(result, "2007-01-25")

    def test_iso8601_adjusts_to_local_time(self):
        # Given a valid date in tz -1hr before midnight
        date = "2007-01-25T23:59:59-0100"

        # When format_date is called
        result = EqPayload()._format_string_long_date_time_to_short_date(date)

        # Then the date is localised to the next day
        self.assertEqual(result, "2007-01-26")

    def test_string_date_time_adjusts_to_local_time_iso_format(self):
        # Given a valid date in tz -1hr before midnight
        date = "2007-01-25T23:59:59-0100"

        # When format_date is called
        result = EqPayload()._format_string_long_date_time_to_iso_format(date)

        # Then the date is localised to the next day
        self.assertEqual(result, "2007-01-26T00:59:59+00:00")

    def test_generate_eq_url_missing_mandatory_event_date(self):
        # Given a mandatory event date does not exist
        collex_events_dates = [
            {
                "id": "e82e7ec9-b14e-412c-813e-edfd2e03e773",
                "collectionExerciseId": "8d926ae3-fb3c-4c25-9f0f-356ded7d1ac0",
                "tag": "return_by",
                "timestamp": "2018-03-27T01:00:00.000+01:00",
            },
            {
                "id": "8a24731e-3d79-4f3c-b6eb-3b199f53694f",
                "collectionExerciseId": "8d926ae3-fb3c-4c25-9f0f-356ded7d1ac0",
                "tag": "reminder",
                "timestamp": "2018-04-03T01:00:00.000+01:00",
            },
        ]

        # When find_event_date_by_tag is called with a search param
        # Then an InvalidEqPayLoad is raised

        with self.assertRaises(InvalidEqPayLoad) as e:
            EqPayload()._find_event_date_by_tag("return by", collex_events_dates, "123", True)
        self.assertEqual(e.exception.message, "Mandatory event not found for collection 123 for search param return by")

    def test_generate_eq_url_non_mandatory_event_date_is_none(self):
        # Given a non mandatory event date does not exist
        collex_events_dates = []
        # When find_event_date_by_tag is called with a search param
        # Then a None response is returned and no exception is raised

        response = EqPayload()._find_event_date_by_tag("employment", collex_events_dates, "123", False)
        self.assertEqual(response, None)

    def test_generate_eq_url_non_mandatory_event_date_is_returned(self):
        # Given a non mandatory event date exists
        collex_events_dates = [
            {
                "id": "e82e7ec9-b14e-412c-813e-edfd2e03e773",
                "collectionExerciseId": "8d926ae3-fb3c-4c25-9f0f-356ded7d1ac0",
                "tag": "return_by",
                "timestamp": "2018-03-27T01:00:00.000+01:00",
            },
            {
                "id": "8a24731e-3d79-4f3c-b6eb-3b199f53694f",
                "collectionExerciseId": "8d926ae3-fb3c-4c25-9f0f-356ded7d1ac0",
                "tag": "employment",
                "timestamp": "2018-04-03T01:00:00.000+01:00",
            },
        ]
        # When find_event_date_by_tag is called with a search param
        # Then the formatted date is returned

        response = EqPayload()._find_event_date_by_tag("employment", collex_events_dates, "123", False)
        self.assertEqual(response, "2018-04-03")

    @freeze_time(TIME_TO_FREEZE)
    @requests_mock.mock()
    def test_create_payload_with_supplementary_data(self, mock_request):
        # Given a collection exercise contains supplementary data
        collection_exercise_with_supplementary_dataset
        mock_request.get(url_get_collection_exercise_events, json=collection_exercise_events)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_ci, json=collection_instrument_eq)
        mock_request.get(url_registry_instrument, json=registry_instrument)
        # When a payload is created
        with app.app_context():
            payload_created = EqPayload().create_payload(
                case,
                collection_exercise_with_supplementary_dataset,
                respondent_party["id"],
                business_party["id"],
                survey_eq,
            )

        # Then the payload is as expected
        self.maxDiff = 1000
        self.assertIn(
            "b9a87999-fcc0-4085-979f-06390fb5dddd", payload_created["survey_metadata"]["data"]["sds_dataset_id"]
        )

    @freeze_time(TIME_TO_FREEZE)
    @requests_mock.mock()
    def test_create_payload_with_supplementary_data_but_different_form_type(self, mock_request):
        # Given a collection exercise contains supplementary data
        different_form_type = {
            "supplementaryDatasetJson": '{"survey_id":"001","period_id":"220823",'
            '"form_types":["0002","1234"],'
            '"title":"Test dataset for survey id 009 period 220823",'
            '"sds_published_at":"2023-08-22T14:46:36Z","total_reporting_units":2,'
            '"schema_version":"v1.0.0","sds_dataset_version":4,'
            '"filename":"373d9a77-2ee5-4c1f-a6dd-8d07b0ea9793.json",'
            '"dataset_id":"b9a87999-fcc0-4085-979f-06390fb5dddd"}'
        }
        collection_exercise_with_supplementary_dataset["supplementaryDatasetJson"] = different_form_type
        mock_request.get(url_get_collection_exercise_events, json=collection_exercise_events)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_ci, json=collection_instrument_eq)
        mock_request.get(url_registry_instrument, json=registry_instrument)
        # When a payload is created
        with app.app_context():
            payload_created = EqPayload().create_payload(
                case,
                collection_exercise_with_supplementary_dataset,
                respondent_party["id"],
                business_party["id"],
                survey_eq,
            )

        # Then the payload is as expected
        self.assertNotIn("b9a87999-fcc0-4085-979f-06390fb5dddd", payload_created["survey_metadata"]["data"])

    @requests_mock.mock()
    def test_collection_with_registry_instrument(self, mock_request):
        # Given a collection exercise is without a registry instrument
        mock_request.get(url_get_collection_exercise_events, json=collection_exercise_events)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_ci, json=collection_instrument_eq)
        mock_request.get(url_registry_instrument, json=registry_instrument)

        # When a payload is created
        with app.app_context():
            response_mock = MagicMock()
            logger_mock = MagicMock()
            with patch(
                "frontstage.controllers.collection_instrument_controller.get_registry_instrument",
                Mock(side_effect=ApiError(logger_mock, response_mock)),
            ):
                with self.assertRaises(ApiError):
                    payload_created = EqPayload().create_payload(
                        case, collection_exercise, respondent_party["id"], business_party["id"], survey_eq
                    )

                    # Then the payload is as expected and doesn't have a registry version
                    self.assertTrue(PAYLOAD.items() <= payload_created.items())
                    self.assertIn("8d990a74-5f07-4765-ac66-df7e1a96505b", payload_created)
                    self.assertIn("cir_instrument_id", payload_created)

    @requests_mock.mock()
    def test_collection_without_registry_instrument(self, mock_request):
        # Given a collection exercise is without a registry instrument
        mock_request.get(url_get_collection_exercise_events, json=collection_exercise_events)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_ci, json=collection_instrument_eq)

        # When a payload is created
        with app.app_context():
            response_mock = MagicMock()
            logger_mock = MagicMock()
            with patch(
                "frontstage.controllers.collection_instrument_controller.get_registry_instrument",
                Mock(side_effect=ApiError(logger_mock, response_mock)),
            ):
                with self.assertRaises(ApiError):
                    payload_created = EqPayload().create_payload(
                        case, collection_exercise, respondent_party["id"], business_party["id"], survey_eq
                    )

                    # Then the payload is as expected and doesn't have a registry version
                    self.assertTrue(PAYLOAD.items() <= payload_created.items())
                    self.assertIn("8d990a74-5f07-4765-ac66-df7e1a96505b", payload_created)
                    self.assertNotIn("cir_instrument_id", payload_created)


def _is_valid_uuid(uuid_string: str) -> bool:
    try:
        uuid.UUID(uuid_string, version=4)
    except ValueError:
        return False
    return True
