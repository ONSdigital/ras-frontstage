import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from tests.integration.mocked_services import encoded_jwt_token, respondent_party, url_banner_api, url_auth_token, \
    url_password_change


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
        self.auth_error = {
            'detail': 'Unauthorized user credentials'
        }

    def tearDown(self):
        self.patcher.stop()

    @requests_mock.mock()
    def test_account_password_change_option_select(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)

        response = self.app.post('/my-account', data={"option": 'change_password'}, follow_redirects=True)
        self.assertEqual(response.status_code, 204)
        self.assertTrue('Change your password'.encode() in response.data)
        self.assertTrue('Enter your current password'.encode() in response.data)
        self.assertTrue('Your password must have:'.encode() in response.data)
        self.assertTrue('at least 8 characters'.encode() in response.data)
        self.assertTrue('at least 1 uppercase letter'.encode() in response.data)
        self.assertTrue('at least 1 symbol (eg: ?!£%)'.encode() in response.data)
        self.assertTrue('at least 1 number'.encode() in response.data)
        self.assertTrue('New Password'.encode() in response.data)
        self.assertTrue('Re-type your new password'.encode() in response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    def test_account_password_change_success(self, mock_request, get_respondent_party_by_id):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_auth_token, status_code=204)
        mock_request.put(url_password_change, status_code=200)
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post('/my-account/change-password', data={"password": 'test',
                                                                      "new_password": 'Password123!',
                                                                      "new_password_confirm": 'Password123!'},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Your password has been changed.'.encode() in response.data)
        self.assertTrue('using your enrolment code'.encode() in response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    def test_account_password_change_form_validation_errors_does_not_meet_requirement(self, mock_request,
                                                                                      get_respondent_party_by_id):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_auth_token, status_code=204)
        mock_request.put(url_password_change, status_code=200)
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post('/my-account/change-password', data={"password": 'test',
                                                                      "new_password": 'Password123',
                                                                      "new_password_confirm": 'Password123'},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Your password doesn\'t meet the requirements'.encode() in response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    def test_account_password_change_validation_error(self, mock_request, get_respondent_party_by_id):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_auth_token, status_code=204)
        mock_request.put(url_password_change, status_code=200)
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post('/my-account/change-password', data={},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('There are 2 errors on this page'.encode() in response.data)
        self.assertTrue('Password is required'.encode() in response.data)
        self.assertTrue('New password is required'.encode() in response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    def test_account_password_change_validation_error_old_password_incorrect(self,
                                                                             mock_request,
                                                                             get_respondent_party_by_id):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_auth_token, status_code=401, json=self.auth_error)
        mock_request.put(url_password_change, status_code=200)
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post('/my-account/change-password', data={"password": 'test',
                                                                      "new_password": 'Password123!',
                                                                      "new_password_confirm": 'Password123!'},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('There is 1 error on this page'.encode() in response.data)
        self.assertTrue('Incorrect current password'.encode() in response.data)

    @requests_mock.mock()
    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    def test_account_password_change_validation_error_old_new_password_same(self,
                                                                            mock_request,
                                                                            get_respondent_party_by_id):
        mock_request.get(url_banner_api, status_code=404)
        mock_request.post(url_auth_token, status_code=401, json=self.auth_error)
        mock_request.put(url_password_change, status_code=200)
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post('/my-account/change-password', data={"password": 'Password123!',
                                                                      "new_password": 'Password123!',
                                                                      "new_password_confirm": 'Password123!'},
                                 follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('There is 1 error on this page'.encode() in response.data)
        self.assertTrue('Your new password is the same as your old password'.encode() in response.data)
