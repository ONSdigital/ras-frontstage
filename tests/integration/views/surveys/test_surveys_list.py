import json
import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from tests.integration.mocked_services import (
    encoded_jwt_token,
    respondent_party,
    survey_list_history,
    survey_list_todo,
    url_banner_api,
)

with open("tests/test_data/party/no_association_party.json") as fp:
    respondent_party_no_association = json.load(fp)


@requests_mock.mock()
class TestSurveyList(unittest.TestCase):
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

    @patch("frontstage.controllers.party_controller.get_survey_list_details_for_party")
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    def test_survey_list_todo(self, mock_request, get_respondent_party_by_id, get_survey_list):
        mock_request.get(url_banner_api, status_code=404)
        get_survey_list.return_value = survey_list_todo
        get_respondent_party_by_id.return_value = respondent_party

        response = self.app.get("/surveys/todo")

        self.assertEqual(response.status_code, 200)

    @patch("frontstage.controllers.party_controller.get_survey_list_details_for_party")
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    def test_survey_list_history(self, mock_request, get_respondent_party_by_id, get_survey_list):
        mock_request.get(url_banner_api, status_code=404)
        get_survey_list.return_value = survey_list_history
        get_respondent_party_by_id.return_value = respondent_party

        response = self.app.get("/surveys/history")

        self.assertEqual(response.status_code, 200)

    @patch("frontstage.controllers.party_controller.get_survey_list_details_for_party")
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    def test_survey_list_todo_when_no_association(self, mock_request, get_respondent_party_by_id, get_survey_list):
        mock_request.get(url_banner_api, status_code=404)
        get_survey_list.return_value = {}
        get_respondent_party_by_id.return_value = respondent_party_no_association
        response = self.app.get("/surveys/todo")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            "There are no surveys registered to your account. If you wish to delete your account".encode()
            in response.data
        )
        self.assertTrue("Click on the survey name to complete your questionnaire.".encode() in response.data)
        self.assertTrue("Need to add a new survey? Use your enrolment code to".encode() in response.data)

    @patch("frontstage.controllers.party_controller.get_survey_list_details_for_party")
    @patch("frontstage.controllers.party_controller.get_respondent_party_by_id")
    def test_survey_list_todo_when_association(self, mock_request, get_respondent_party_by_id, get_survey_list):
        mock_request.get(url_banner_api, status_code=404)
        get_survey_list.return_value = {}
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.get("/surveys/todo")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            "There are no surveys registered to your account. If you wish to delete your account".encode()
            in response.data
        )
        self.assertTrue("Click on the survey name to complete your questionnaire.".encode() in response.data)
        self.assertTrue("Need to add a new survey? Use your enrolment code to".encode() in response.data)
