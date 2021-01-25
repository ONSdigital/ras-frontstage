import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from tests.integration.mocked_services import encoded_jwt_token, respondent_party, survey_list_todo


class TestSurveyList(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie('localhost', 'authorization', 'session_key')
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"
            # NOQA
        }
        self.patcher = patch('redis.StrictRedis.get', return_value=encoded_jwt_token)
        self.contact_details_form = {
            "option": "contact_details"
        }
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    def test_account(self, get_respondent_party_by_id):
        get_respondent_party_by_id.return_value = respondent_party

        response = self.app.get('/my-account')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('example@example.com'.encode() in response.data)
        self.assertTrue('0987654321'.encode() in response.data)

    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    def test_account_options(self, get_respondent_party_by_id):
        get_respondent_party_by_id.return_value = respondent_party

        response = self.app.get('/my-account')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('example@example.com'.encode() in response.data)
        self.assertTrue('0987654321'.encode() in response.data)
        self.assertIn("Help with your account".encode(), response.data)

    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    def test_account_options_not_selection(self, get_respondent_party_by_id):
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post('/my-account', data={"option": None}, follow_redirects=True)
        self.assertIn("At least one option should be selected.".encode(),
                      response.data)

    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    def test_account_options_selection(self, get_respondent_party_by_id):
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post('/my-account', data=self.contact_details_form, follow_redirects=True)
        self.assertIn("For international numbers include the country code, for example +33 1234 567 890".encode(),
                      response.data)

    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    def test_account_contact_details_error(self, get_respondent_party_by_id):
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post('/my-account/change-account-details',
                                 data={"first_name": ""}, follow_redirects=True)
        self.assertIn("Problem with the first name".encode(), response.data)

    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    @patch('frontstage.controllers.party_controller.update_account')
    @patch('frontstage.controllers.party_controller.get_survey_list_details_for_party')
    def test_account_contact_details_success(self,
                                             get_survey_list,
                                             update_account,
                                             get_respondent_party_by_id):
        get_respondent_party_by_id.return_value = respondent_party
        get_survey_list.return_value = survey_list_todo
        response = self.app.post('/my-account/change-account-details',
                                 data={"first_name": "test account",
                                       "last_name": "test_account",
                                       "phone_number": "07772257773"}, follow_redirects=True)
        self.assertIn("We&#39;ve updated your first name, last name and telephone number".encode(), response.data)
