import io
import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from tests.integration.mocked_services import (
    business_party,
    case,
    categories,
    collection_exercise,
    collection_exercise_events,
    collection_exercise_v3,
    collection_instrument_eq,
    collection_instrument_seft,
    completed_case,
    encoded_jwt_token,
    encrypted_enrolment_code,
    respondent_party,
    survey,
    survey_eq,
    url_banner_api,
    url_get_business_party,
    url_get_case,
    url_get_case_categories,
    url_get_ci,
    url_get_collection_exercise,
    url_get_collection_exercise_events,
    url_get_respondent_party,
    url_get_survey_by_short_name_eq,
    url_post_case_event_uuid,
)

party_id = "0008279d-9425-4e28-897d-bfd876aa7f3f"
case_id = "8cdc01f9-656a-4715-a148-ffed0dbe1b04"


@requests_mock.mock()
class TestAccessSurvey(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie("localhost", "authorization", "session_key")
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb"
            "20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnX"
            "zRbEKoqXb8Q5U9VVdy54"
            # NOQA
        }
        self.survey_file = dict(file=(io.BytesIO(b"my file contents"), "testfile.xlsx"))
        self.upload_error = {"error": {"data": {"message": ".xlsx format"}}}
        self.patcher = patch("redis.StrictRedis.get", return_value=encoded_jwt_token)
        self.params = {"encrypted_enrolment_code": encrypted_enrolment_code}
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @patch("frontstage.controllers.case_controller.get_case_data")
    def test_access_survey_all_expected_case_data(self, mock_request, get_case_data):
        mock_request.get(url_banner_api, status_code=404)
        case_data = {
            "collection_exercise": collection_exercise,
            "collection_instrument": collection_instrument_seft,
            "survey": survey,
            "business_party": business_party,
        }
        get_case_data.return_value = case_data

        response = self.app.get(
            f"/surveys/access-survey?case_id={case_id}&business_party_id={party_id}&"
            "survey_short_name=Bricks&ci_type=SEFT",
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(survey["shortName"].encode(), response.data)

    @patch("frontstage.controllers.case_controller.get_case_data")
    def test_access_survey_missing_collection_instrument_from_case_data(self, mock_request, get_case_data):
        mock_request.get(url_banner_api, status_code=404)
        case_data = {"collection_exercise": collection_exercise, "survey": survey, "business_party": business_party}
        get_case_data.return_value = case_data
        response = self.app.get(
            f"/surveys/access-survey?case_id={case_id}&business_party_id={party_id}&"
            "survey_short_name=Bricks&ci_type=SEFT",
            headers=self.headers,
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 500)
        self.assertTrue("An error has occurred".encode() in response.data)

    @patch("frontstage.controllers.case_controller.get_case_data")
    def test_access_survey_missing_collection_exercise_from_case_data(self, mock_request, get_case_data):
        mock_request.get(url_banner_api, status_code=404)
        case_data = {
            "collection_instrument": collection_instrument_seft,
            "survey": survey,
            "business_party": business_party,
        }
        get_case_data.return_value = case_data
        response = self.app.get(
            f"/surveys/access-survey?case_id={case_id}&business_party_id={party_id}&"
            "survey_short_name=Bricks&ci_type=SEFT",
            headers=self.headers,
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 500)
        self.assertTrue("An error has occurred".encode() in response.data)

    @patch("frontstage.controllers.case_controller.get_case_data")
    def test_access_survey_missing_survey_from_case_data(self, mock_request, get_case_data):
        mock_request.get(url_banner_api, status_code=404)
        case_data = {
            "collection_exercise": collection_exercise,
            "collection_instrument": collection_instrument_seft,
            "business_party": business_party,
        }
        get_case_data.return_value = case_data

        response = self.app.get(
            f"/surveys/access-survey?case_id={case_id}&business_party_id={party_id}&"
            "survey_short_name=Bricks&ci_type=SEFT",
            headers=self.headers,
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 500)
        self.assertTrue("An error has occurred".encode() in response.data)

    @patch("frontstage.controllers.case_controller.get_case_data")
    def test_access_survey_missing_business_party_from_case_data(self, mock_request, get_case_data):
        mock_request.get(url_banner_api, status_code=404)
        case_data = {
            "collection_exercise": collection_exercise,
            "collection_instrument": collection_instrument_seft,
            "survey": survey,
        }
        get_case_data.return_value = case_data

        response = self.app.get(
            f"/surveys/access-survey?case_id={case_id}&business_party_id={party_id}&"
            "survey_short_name=Bricks&ci_type=SEFT",
            headers=self.headers,
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 500)
        self.assertTrue("An error has occurred".encode() in response.data)

    def test_access_survey_without_request_arg_case_id(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get(
            f"/surveys/access-survey?business_party_id={party_id}&" "survey_short_name=Bricks&ci_type=SEFT",
            headers=self.headers,
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue("An error has occurred".encode() in response.data)

    def test_access_survey_missing_request_arg_business_party_id(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get(
            f"/surveys/access-survey?case_id={case_id}&" "survey_short_name=Bricks&ci_type=SEFT", headers=self.headers
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue("An error has occurred".encode() in response.data)

    def test_access_survey_missing_request_arg_survey_short_name(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get(
            f"/surveys/access-survey?case_id={case_id}&business_party_id={party_id}&" "ci_type=SEFT",
            headers=self.headers,
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue("An error has occurred".encode() in response.data)

    def test_access_survey_missing_request_arg_ci_type(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get(
            f"/surveys/access-survey?case_id={case_id}&business_party_id={party_id}&" "survey_short_name=Bricks",
            headers=self.headers,
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue("An error has occurred".encode() in response.data)

    def test_generate_eq_url(self, mock_request):
        # Given all external services are mocked, and we have an EQ collection instrument
        mock_request.get(url_get_case, json=case)
        mock_request.get(url_get_collection_exercise, json=collection_exercise_v3)
        mock_request.get(url_get_collection_exercise_events, json=collection_exercise_events)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey_by_short_name_eq, json=survey_eq)
        mock_request.get(url_get_ci, json=collection_instrument_eq)
        mock_request.get(url_get_case_categories, json=categories)
        mock_request.post(url_post_case_event_uuid, status_code=201)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_banner_api, status_code=404)

        # When the generate-eq-url is called
        response = self.app.get(
            f"/surveys/access-survey?case_id={case['id']}&business_party_id={business_party['id']}"
            f"&survey_short_name={survey_eq['shortName']}&ci_type=EQ",
            headers=self.headers,
        )

        # An eq url is generated
        self.assertEqual(response.status_code, 302)
        self.assertIn("https://eq-test/v3/session?token=", response.location)

    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    def test_generate_eq_url_complete_case(self, mock_request, _):
        # Given a mocked case has its caseGroup status as complete
        mock_request.get(
            f"{app.config['COLLECTION_EXERCISE_URL']}" f"/collectionexercises/14fb3e68-4dca-46db-bf49-04b84e07e77c",
            json=collection_exercise,
        )
        mock_request.get(f"{app.config['CASE_URL']}/cases/8cdc01f9-656a-4715-a148-ffed0dbe1b04", json=completed_case)
        mock_request.get(url_get_collection_exercise_events, json=collection_exercise_events)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey_by_short_name_eq, json=survey_eq)
        mock_request.get(url_get_ci, json=collection_instrument_eq)
        mock_request.get(url_get_case_categories, json=categories)
        mock_request.post(url_post_case_event_uuid, status_code=201)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_banner_api, status_code=404)

        # When the generate-eq-url is called
        response = self.app.get(
            f"/surveys/access-survey?case_id={completed_case['id']}&business_party_id={business_party['id']}"
            f"&survey_short_name={survey_eq['shortName']}&ci_type=EQ",
            headers=self.headers,
            follow_redirects=True,
        )

        # A 403 is returned
        self.assertEqual(response.status_code, 403)

    @patch("frontstage.controllers.party_controller.is_respondent_enrolled")
    def test_generate_eq_v3_url_complete_case(self, mock_request, _):
        # Given a mocked case has its caseGroup status as complete
        mock_request.get(
            f"{app.config['COLLECTION_EXERCISE_URL']}" f"/collectionexercises/14fb3e68-4dca-46db-bf49-04b84e07e77c",
            json=collection_exercise_v3,
        )
        mock_request.get(f"{app.config['CASE_URL']}/cases/8cdc01f9-656a-4715-a148-ffed0dbe1b04", json=completed_case)
        mock_request.get(url_get_collection_exercise_events, json=collection_exercise_events)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey_by_short_name_eq, json=survey_eq)
        mock_request.get(url_get_ci, json=collection_instrument_eq)
        mock_request.get(url_get_case_categories, json=categories)
        mock_request.post(url_post_case_event_uuid, status_code=201)
        mock_request.get(url_get_respondent_party, status_code=200, json=respondent_party)
        mock_request.get(url_banner_api, status_code=404)

        # When the generate-eq-url is called
        response = self.app.get(
            f"/surveys/access-survey?case_id={completed_case['id']}&business_party_id={business_party['id']}"
            f"&survey_short_name={survey_eq['shortName']}&ci_type=EQ",
            headers=self.headers,
            follow_redirects=True,
        )

        # A 403 is returned
        self.assertEqual(response.status_code, 403)
