import json
import unittest
from unittest.mock import patch

from frontstage import app
from tests.app.mocked_services import business_party, case, collection_instrument_seft, encoded_jwt_token, survey


class TestDownloadSurvey(unittest.TestCase):

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

    @patch('frontstage.controllers.collection_instrument_controller.download_collection_instrument')
    @patch('frontstage.controllers.case_controller.check_case_permissions')
    @patch('frontstage.controllers.case_controller.get_case_by_case_id')
    def test_download_survey_success(self, get_case_by_id, _, download_collection_instrument):
        str = json.dumps(collection_instrument_seft)
        binary = ' '.join(format(ord(letter), 'b') for letter in str)
        get_case_by_id.return_value = case
        headers = {'Content-type': 'application/json', 'Content-Length': '5962'}
        download_collection_instrument.return_value = binary, headers

        response = self.app.get(f'/surveys/download_survey?case_id={case["id"]}&business_party_id={business_party["id"]}'
                                f'&survey_short_name={survey["shortName"]}')

        self.assertEqual(response.status_code, 200)
