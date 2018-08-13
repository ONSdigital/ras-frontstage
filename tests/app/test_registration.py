import unittest

import requests_mock

from frontstage import app
from tests.app.mocked_services import (business_party, case, categories, collection_exercise,
                                       encrypted_enrolment_code, enrolment_code, survey, token,
                                       url_get_case_by_enrolment_code, url_get_business_party,
                                       url_get_case_categories, url_get_collection_exercise,
                                       url_get_survey, url_post_case_event_uuid, url_create_account,
                                       url_validate_enrolment, url_verify_email)


class TestRegistration(unittest.TestCase):

    def setUp(self):

        self.app = app.test_client()
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
            }
        self.test_user = {
            'first_name': 'john',
            'last_name': 'doe',
            'email_address': 'testuser2@email.com',
            'password': 'Password123!',
            'password_confirm': 'Password123!',
            'phone_number': '07717275049'
            }
        self.organisation_survey_data = {
            'survey_name': 'test_survey',
            'organisation_name': 'test_org'
        }
        self.params = {
            "encrypted_enrolment_code": encrypted_enrolment_code
        }

    def test_view_enrolment_code_page(self):
        response = self.app.get('/register/create-account')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Create an account'.encode() in response.data)
        self.assertTrue('Enrolment Code'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_enrolment_code_success(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, json=case)
        mock_object.get(url_get_case_categories, json=categories)
        mock_object.post(url_post_case_event_uuid, status_code=201)
        mock_object.post(url_create_account)

        response = self.app.post('/register/create-account', data={'enrolment_code': enrolment_code})

        # Check that we redirect to the confirm-organisation-survey page
        self.assertEqual(response.status_code, 302)
        self.assertTrue('confirm-organisation-survey'.encode() in response.data)

    def test_enter_enrolment_code_no_enrolment_code(self):
        response = self.app.post('/register/create-account')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Create an account'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_enrolment_code_inactive_code(self, mock_object):
        mock_object.get(url_validate_enrolment, status_code=401, json={'active': False})

        response = self.app.post('/register/create-account', data={'enrolment_code': enrolment_code})

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Enrolment code not valid'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_enrolment_code_already_used(self, mock_object):
        mock_object.get(url_validate_enrolment, status_code=400)

        response = self.app.post('/register/create-account', data={'enrolment_code': enrolment_code})

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Enrolment code not valid'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_enrolment_code_invalid_code(self, mock_object):
        mock_object.get(url_validate_enrolment, status_code=404)

        response = self.app.post('/register/create-account', data={'enrolment_code': enrolment_code})

        self.assertEqual(response.status_code, 202)
        self.assertTrue('Enrolment code not valid'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_enrolment_code_fail(self, mock_object):
        mock_object.get(url_validate_enrolment, status_code=500)

        response = self.app.post('/register/create-account', data={'enrolment_code': enrolment_code}, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    # ============== CONFIRM ORG AND SURVEY ===============
    @requests_mock.mock()
    def test_confirm_org_page(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, json=case)
        mock_object.get(url_get_business_party, json=business_party)
        mock_object.get(url_get_collection_exercise, json=collection_exercise)
        mock_object.get(url_get_survey, json=survey)

        response = self.app.get('/register/create-account/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Confirm organisation'.encode() in response.data)

    @requests_mock.mock()
    def test_confirm_org_page_validation_fail(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': False, 'caseId': case['id']})

        response = self.app.get('/register/create-account/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_confirm_org_page_case_fail(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, status_code=500)

        response = self.app.get('/register/create-account/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_confirm_org_page_case_empty(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, json={})

        response = self.app.get('/register/create-account/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_confirm_org_page_party_fail(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, json=case)
        mock_object.get(url_get_business_party, status_code=500)

        response = self.app.get('/register/create-account/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_confirm_org_page_collex_fail(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, json=case)
        mock_object.get(url_get_business_party, json=business_party)
        mock_object.get(url_get_collection_exercise, status_code=500)

        response = self.app.get('/register/create-account/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_confirm_org_page_collex_empty(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, json=case)
        mock_object.get(url_get_business_party, json=business_party)
        mock_object.get(url_get_collection_exercise, json={})

        response = self.app.get('/register/create-account/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_confirm_org_page_survey_fail(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, json=case)
        mock_object.get(url_get_business_party, json=business_party)
        mock_object.get(url_get_collection_exercise, json=collection_exercise)
        mock_object.get(url_get_survey, status_code=500)

        response = self.app.get('/register/create-account/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_confirm_org_page_survey_empty(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, json=case)
        mock_object.get(url_get_business_party, json=business_party)
        mock_object.get(url_get_collection_exercise, json=collection_exercise)
        mock_object.get(url_get_survey, json={})

        response = self.app.get('/register/create-account/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Confirm organisation'.encode() in response.data)

    # ============== ENTER YOUR ACCOUNT DETAILS ===============
    @requests_mock.mock()
    def test_create_account_get_page_with_active_enrolment_code(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})

        response = self.app.get('/register/create-account/enter-account-details',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Enter your account details'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_get_page_with_inactive_enrolment_code(self, mock_object):
        mock_object.get(url_validate_enrolment, status_code=401)

        response = self.app.get('/register/create-account/enter-account-details',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_no_email_address(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        del self.test_user['email_address']

        response = self.app.post('/register/create-account/enter-account-details',
                                 query_string=self.params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Enter your account details'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_space_in_email_address(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        self.test_user['email_address'] = 'testuser 2@email.com'

        response = self.app.post('/register/create-account/enter-account-details',
                                 query_string=self.params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue("Your email should be of the form myname@email.com".encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_no_password(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        del self.test_user['password']
        del self.test_user['password_confirm']

        response = self.app.post('register/create-account/enter-account-details',
                                 query_string=self.params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please check the passwords'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_wrong_password(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        self.test_user['password_confirm'] = 'wrongpassword'

        response = self.app.post('register/create-account/enter-account-details',
                                 query_string=self.params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please check the passwords'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_no_phone_number(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        del self.test_user['phone_number']

        response = self.app.post('register/create-account/enter-account-details',
                                 query_string=self.params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please check the phone number'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_illegal_phone_number(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        self.test_user['phone_number'] = 'not a number'

        response = self.app.post('register/create-account/enter-account-details',
                                 query_string=self.params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please check the phone number'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_phone_number_too_small(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        self.test_user['phone_number'] = '12345678'

        response = self.app.post('register/create-account/enter-account-details',
                                 query_string=self.params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please check the phone number'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_register_phone_number_too_big(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        self.test_user['phone_number'] = '1234567890123456'

        response = self.app.post('register/create-account/enter-account-details',
                                 query_string=self.params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please check the phone number'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_success(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.post(url_create_account, status_code=201)

        response = self.app.post('register/create-account/enter-account-details',
                                 query_string=self.params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Almost done'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_duplicate_email(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.post(url_create_account, status_code=400)

        response = self.app.post('register/create-account/enter-account-details',
                                 query_string=self.params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('This email has already been used'.encode() in response.data)

    @requests_mock.mock()
    def test_create_account_fail(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.post(url_create_account, status_code=500)

        response = self.app.post('register/create-account/enter-account-details',
                                 query_string=self.params,
                                 data=self.test_user,
                                 headers=self.headers,
                                 follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    def test_check_email_page(self):
        response = self.app.get('register/create-account/check-email', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Almost done...'.encode() in response.data)

    # ============== ACTIVATE ACCOUNT ===============
    @requests_mock.mock()
    def test_activate_account_success(self, mock_object):
        mock_object.put(url_verify_email)

        response = self.app.get(f'/register/activate-account/{token}', headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('You\'ve activated your account'.encode() in response.data)

    @requests_mock.mock()
    def test_activate_account_token_expired(self, mock_object):
        mock_object.put(url_verify_email, status_code=409)

        response = self.app.get(f'/register/activate-account/{token}', headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Your link has expired'.encode() in response.data)

    @requests_mock.mock()
    def test_activate_account_token_not_found(self, mock_object):
        mock_object.put(url_verify_email, status_code=404)

        response = self.app.get(f'/register/activate-account/{token}', headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 404)
        self.assertTrue('404'.encode() in response.data)

    @requests_mock.mock()
    def test_activate_account_fail(self, mock_object):
        mock_object.put(url_verify_email, status_code=500)

        response = self.app.get(f'/register/activate-account/{token}', headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)
