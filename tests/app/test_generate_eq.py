import json
import requests_mock
import unittest
from unittest.mock import patch

from frontstage import app
from frontstage.common.eq_payload import EqPayload
from frontstage.controllers import collection_exercise_controller
from frontstage.exceptions.exceptions import ApiError, InvalidEqPayLoad

from tests.app.mocked_services import (case, collection_exercise, collection_exercise_events,
                                       business_party, survey, collection_instrument_eq,
                                       url_get_case, url_get_collection_exercise,
                                       url_get_collection_exercise_events, url_get_business_party, url_get_survey,
                                       url_get_ci, collection_instrument_seft, url_post_case_event_uuid,
                                       url_get_case_categories, categories, completed_case)


encoded_jwt_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoicmVzcG9uZGVudCIsImFjY2Vzc190b2tlbiI6ImI5OWIyMjA" \
                    "0LWYxMDAtNDcxZS1iOTQ1LTIyN2EyNmVhNjljZCIsInJlZnJlc2hfdG9rZW4iOiIxZTQyY2E2MS02ZDBkLTQxYjMtODU2Yy0" \
                    "2YjhhMDhlYmIyZTMiLCJleHBpcmVzX2F0IjoxNzM4MTU4MzI4LjAsInBhcnR5X2lkIjoiZjk1NmU4YWUtNmUwZi00NDE0LWI" \
                    "wY2YtYTA3YzFhYTNlMzdiIn0.7W9yikGtX2gbKLclxv-dajcJ2NL0Nb_HDVqHrCrYvQE"


class TestGenerateEqURL(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie('localhost', 'authorization', 'session_key')
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
        }
        self.patcher = patch('redis.StrictRedis.get', return_value=encoded_jwt_token)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @requests_mock.mock()
    def test_generate_eq_url(self, mock_request):

        # Given all external services are mocked and we have an EQ collection instrument
        mock_request.get(url_get_case, json=case)
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_events, json=collection_exercise_events)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_eq)
        mock_request.get(url_get_case_categories, json=categories)
        mock_request.post(url_post_case_event_uuid, status_code=201)

        # When the generate-eq-url is called
        response = self.app.get(f"/surveys/access_survey?case_id={case['id']}&ci_type=EQ", headers=self.headers)

        # An eq url is generated
        self.assertEqual(response.status_code, 302)
        self.assertIn("https://eq-test/session?token=", response.location)

    @requests_mock.mock()
    def test_generate_eq_url_complete_case(self, mock_request):

        # Given a mocked case has its caseGroup status as complete
        mock_request.get(url_get_case, json=completed_case)

        # When the generate-eq-url is called
        response = self.app.get(f"/surveys/access_survey?case_id={completed_case['id']}&ci_type=EQ", headers=self.headers, follow_redirects=True)

        # A 403 is returned
        self.assertEqual(response.status_code, 403)

    @requests_mock.mock()
    def test_generate_eq_url_seft(self, mock_request):

        # Given all external services are mocked and we have seft collection instrument
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_events, json=collection_exercise_events)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_seft)

        # When create_payload is called
        # Then an InvalidEqPayLoad is raised
        with app.app_context():
            with self.assertRaises(InvalidEqPayLoad) as e:
                EqPayload().create_payload(case)
        self.assertEqual(e.exception.message, 'Collection instrument 68ad4018-2ddd-4894-89e7-33f0135887a2 type is not EQ')

    @requests_mock.mock()
    def test_generate_eq_url_no_eq_id(self, mock_request):

        # Given all external services are mocked and we have an EQ collection instrument without an EQ ID
        with open('tests/test_data/collection_instrument/collection_instrument_eq_no_eq_id.json') as json_data:
            collection_instrument_eq_no_eq_id = json.load(json_data)

        mock_request.get(url_get_ci, json=collection_instrument_eq_no_eq_id)

        # When create_payload is called
        # Then an InvalidEqPayLoad is raised
        with app.app_context():
            with self.assertRaises(InvalidEqPayLoad) as e:
                EqPayload().create_payload(case)
        self.assertEqual(e.exception.message, 'Collection instrument 68ad4018-2ddd-4894-89e7-33f0135887a2 '
                                            'classifiers are incorrect or missing')

    @requests_mock.mock()
    def test_generate_eq_url_no_form_type(self, mock_request):

        # Given all external services are mocked and we have an EQ collection instrument without a Form_type
        with open('tests/test_data/collection_instrument/collection_instrument_eq_no_form_type.json') as json_data:
            collection_instrument_eq_no_form_type = json.load(json_data)

        mock_request.get(url_get_ci, json=collection_instrument_eq_no_form_type)

        # When create_payload is called
        # Then an InvalidEqPayLoad is raised
        with app.app_context():
            with self.assertRaises(InvalidEqPayLoad) as e:
                EqPayload().create_payload(case)
        self.assertEqual(e.exception.message, 'Collection instrument 68ad4018-2ddd-4894-89e7-33f0135887a2 '
                                            'classifiers are incorrect or missing')

    @requests_mock.mock()
    def test_access_collection_exercise_events_fail(self, mock_request):

        # Given a failing collection exercise events service
        mock_request.get(url_get_collection_exercise_events, status_code=500)
        collection_exercise_id = '14fb3e68-4dca-46db-bf49-04b84e07e77c'

        # When get collection exercise events is called
        # Then an ApiError is raised
        with app.app_context():
            with self.assertRaises(ApiError):
                collection_exercise_controller.get_collection_exercise_events(collection_exercise_id)

    def test_generate_eq_url_incorrect_date_format(self):

        # Given an invalid date
        date = 'invalid'

        # When format_string_long_date_time_to_short_date is called
        # Then an InvalidEqPayLoad is raised
        with self.assertRaises(InvalidEqPayLoad) as e:
            EqPayload()._format_string_long_date_time_to_short_date(date)
        self.assertEqual(e.exception.message, 'Unable to format invalid')

    def test_generate_eq_url_iso8601_date_format(self):

        # Given an invalid date
        date = '2007-01-25T12:00:00Z'

        # When format_string_long_date_time_to_short_date is called
        # Then an InvalidEqPayLoad is raised
        result = EqPayload()._format_string_long_date_time_to_short_date(date)
        self.assertEqual(result, '2007-01-25')

    def test_generate_eq_url_missing_event_date(self):

        # Given no event dates
        collex_events_dates = []
        # When find_event_date_by_tag is called with a search param
        # Then an InvalidEqPayLoad is raised

        with self.assertRaises(InvalidEqPayLoad) as e:
            EqPayload()._find_event_date_by_tag('return by', collex_events_dates, '123')
        self.assertEqual(e.exception.message, 'Event not found for collection 123 for search param return by')
