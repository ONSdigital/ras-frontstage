import json
import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from frontstage.common.eq_payload import EqPayload
from frontstage.controllers import collection_exercise_controller
from frontstage.exceptions.exceptions import ApiError, InvalidEqPayLoad
from tests.integration.mocked_services import (
    business_party,
    case,
    collection_exercise,
    collection_exercise_events,
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
)

encoded_jwt_token = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwYXJ0eV9pZCI6ImY5NTZlOGFlLTZ"
    "lMGYtNDQxNC1iMGNmLWEwN2MxYWEzZTM3YiIsImV4cGlyZXNfYXQiOiIxMDAxMjM0NTY"
    "3ODkiLCJyb2xlIjoicmVzcG9uZGVudCIsInVucmVhZF9tZXNzYWdlX2NvdW50Ijp7InZh"
    "bHVlIjowLCJyZWZyZXNoX2luIjozMjUyNzY3NDAwMC4wfSwiZXhwaXJlc19pbiI6MzI1M"
    "jc2NzQwMDAuMH0.m94R50EPIKTJmE6gf6PvCmCq8ZpYwwV8PHSqsJh5fnI"
)


class TestGenerateEqURL(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie("localhost", "authorization", "session_key")
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
                    version=None,
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
                    version=None,
                )
        self.assertEqual(
            e.exception.message,
            "Collection instrument 68ad4018-2ddd-4894-89e7-33f0135887a2 " "classifiers are incorrect or missing",
        )

    @requests_mock.mock()
    def test_generate_eq_url_contains_response_id_for_v3(self, mock_request):
        # Given all external services are mocked and we have an EQ collection instrument without an EQ ID
        mock_request.get(url_get_collection_exercise_events, json=collection_exercise_events)
        mock_request.get(url_get_business_party, json=business_party)
        with open("tests/test_data/collection_instrument/collection_instrument_eq.json") as json_data:
            collection_instrument_eq = json.load(json_data)

        mock_request.get(url_get_ci, json=collection_instrument_eq)
        mock_request.get(url_banner_api, status_code=404)

        # When create_payload is called
        # Then an InvalidEqPayLoad is raised
        with app.app_context():
            payload = EqPayload().create_payload(
                case,
                collection_exercise,
                party_id=respondent_party["id"],
                business_party_id=business_party["id"],
                survey=survey_eq,
                version="v3",
            )
        self.assertTrue("response_id" in payload)

    @requests_mock.mock()
    def test_generate_eq_url_for_response_id_for_v2(self, mock_request):
        # Given all external services are mocked and we have an EQ collection instrument without an EQ ID
        mock_request.get(url_get_collection_exercise_events, json=collection_exercise_events)
        mock_request.get(url_get_business_party, json=business_party)
        with open("tests/test_data/collection_instrument/collection_instrument_eq.json") as json_data:
            collection_instrument_eq = json.load(json_data)

        mock_request.get(url_get_ci, json=collection_instrument_eq)
        mock_request.get(url_banner_api, status_code=404)

        # When create_payload is called
        # Then an InvalidEqPayLoad is raised
        with app.app_context():
            payload = EqPayload().create_payload(
                case,
                collection_exercise,
                party_id=respondent_party["id"],
                business_party_id=business_party["id"],
                survey=survey_eq,
                version="v2",
            )
        self.assertFalse("response_id" in payload)

    @requests_mock.mock()
    def test_generate_eq_url_no_form_type(self, mock_request):
        # Given all external services are mocked and we have an EQ collection instrument without a Form_type
        with open("tests/test_data/collection_instrument/collection_instrument_eq_no_form_type.json") as json_data:
            collection_instrument_eq_no_form_type = json.load(json_data)

        mock_request.get(url_get_ci, json=collection_instrument_eq_no_form_type)
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
                    version=None,
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
