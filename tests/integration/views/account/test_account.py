import unittest
import responses
from unittest.mock import patch

from frontstage import app
from tests.integration.mocked_services import encoded_jwt_token, respondent_party, survey_list_todo, \
    url_get_respondent_party


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
        self.assertIn("Help with your account".encode(), response.data)

    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    def test_account_options_not_selection(self, get_respondent_party_by_id):
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post('/my-account', data={"option": None}, follow_redirects=True)
        self.assertIn("At least one option should be selected".encode(),
                      response.data)

    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    def test_account_options_selection(self, get_respondent_party_by_id):
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post('/my-account', data=self.contact_details_form, follow_redirects=True)
        self.assertIn("Phone number".encode(),
                      response.data)

    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    def test_account_contact_details_error(self, get_respondent_party_by_id):
        get_respondent_party_by_id.return_value = respondent_party
        response = self.app.post('/my-account/change-account-details',
                                 data={"first_name": ""}, follow_redirects=True)
        self.assertIn("There are 4 errors on this page".encode(), response.data)
        self.assertIn("Problem with the first name".encode(), response.data)
        self.assertIn("Problem with the phone number".encode(), response.data)
        self.assertIn("Problem with the email address".encode(), response.data)

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
                                 data={"first_name": "new first name",
                                       "last_name": "new last name",
                                       "phone_number": "8882257773",
                                       "email_address": "example@example.com"}, follow_redirects=True)
        self.assertIn("updated your first name, last name and telephone number".encode(), response.data)

    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    @patch('frontstage.controllers.party_controller.get_survey_list_details_for_party')
    @patch('frontstage.controllers.party_controller.is_email_already_used_to_register')
    def test_account_change_account_email_address(self,
                                                  is_email_already_used_to_register,
                                                  get_survey_list,
                                                  get_respondent_party_by_id):
        get_respondent_party_by_id.return_value = respondent_party
        get_survey_list.return_value = survey_list_todo
        is_email_already_used_to_register.return_value = False
        with responses.RequestsMock() as rsps:
            rsps.add(rsps.PUT, url_get_respondent_party, json=respondent_party, status=200)
            response = self.app.post('/my-account/change-account-details',
                                     data={"first_name": "test account",
                                           "last_name": "test_account",
                                           "phone_number": "07772257773",
                                           "email_address": "exampleone@example.com"}, follow_redirects=True)
            self.assertIn("updated your first name, last name and telephone number".encode(), response.data)
            self.assertIn("Change email address".encode(), response.data)
            self.assertIn("You will need to authorise a change of email address.".encode(), response.data)
            self.assertIn("We will send a confirmation email to".encode(), response.data)
            self.assertIn("exampleone@example.com".encode(), response.data)

    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    @patch('frontstage.controllers.party_controller.update_account')
    @patch('frontstage.controllers.party_controller.get_survey_list_details_for_party')
    @patch('frontstage.controllers.party_controller.is_email_already_used_to_register')
    def test_account_change_account_email_addres_almost_done(self,
                                                             is_email_already_used_to_register,
                                                             get_survey_list,
                                                             update_account,
                                                             get_respondent_party_by_id):
        get_respondent_party_by_id.return_value = respondent_party
        get_survey_list.return_value = survey_list_todo
        is_email_already_used_to_register.return_value = False
        response = self.app.post('/my-account/change-account-email-address',
                                 data={"email_address": "exampleone@example.com"}, follow_redirects=True)
        self.assertIn("Almost done".encode(), response.data)
        self.assertIn("Once you have received it, you need to follow the link".encode(), response.data)
        self.assertIn("please call 0300 1234 931".encode(), response.data)

    @patch('frontstage.controllers.party_controller.get_respondent_party_by_id')
    @patch('frontstage.controllers.party_controller.update_account')
    @patch('frontstage.controllers.party_controller.get_survey_list_details_for_party')
    @patch('frontstage.controllers.party_controller.is_email_already_used_to_register')
    def test_email_already_in_use(self,
                                  is_email_already_used_to_register,
                                  get_survey_list,
                                  update_account,
                                  get_respondent_party_by_id):
        get_respondent_party_by_id.return_value = respondent_party
        get_survey_list.return_value = survey_list_todo
        is_email_already_used_to_register.return_value = True
        response = self.app.post('/my-account/change-account-details',
                                 data={"first_name": "new first name",
                                       "last_name": "new last name",
                                       "phone_number": "8882257773",
                                       "email_address": "something@something.com"}, follow_redirects=True)
        self.assertIn("This email has already been used to register an account".encode(), response.data)