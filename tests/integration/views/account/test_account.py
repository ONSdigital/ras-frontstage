import unittest
from unittest.mock import patch
import requests_mock

from frontstage import app
from tests.integration.mocked_services import encoded_jwt_token, respondent_party, url_banner_api


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

    @requests_mock.mock()
    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    def test_account(self, mock_request, get_respondent_party_by_id):
        mock_request.get(url_banner_api, status_code=204)
        get_respondent_party_by_id.return_value = respondent_party

        response = self.app.get('/my-account')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('example@example.com'.encode() in response.data)
        self.assertTrue('0987654321'.encode() in response.data)
