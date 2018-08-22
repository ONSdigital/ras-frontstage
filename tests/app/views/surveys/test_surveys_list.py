import unittest
from unittest.mock import patch

from frontstage import app
from tests.app.mocked_services import encoded_jwt_token, survey_list_history, survey_list_todo


class TestSurveyList(unittest.TestCase):

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

    @patch('frontstage.controllers.party_controller.get_survey_list_details_for_party')
    def test_survey_list_todo(self, get_survey_list):
        get_survey_list.return_value = survey_list_todo

        response = self.app.get('/surveys/todo')

        self.assertEqual(response.status_code, 200)

    @patch('frontstage.controllers.party_controller.get_survey_list_details_for_party')
    def test_survey_list_history(self, get_survey_list):
        get_survey_list.return_value = survey_list_history

        response = self.app.get('/surveys/history')

        self.assertEqual(response.status_code, 200)
