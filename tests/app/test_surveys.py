import io
import json
import unittest
from unittest.mock import patch

import flask
import requests
import requests_mock

from frontstage import app
from tests.app.mocked_services import (business_party, case, categories, collection_exercise,
                                       collection_exercise_before_go_live, collection_instrument_seft,
                                       encrypted_enrolment_code, enrolment_code, survey,
                                       url_download_ci, url_get_business_party, url_get_case,
                                       url_get_case_by_enrolment_code, url_get_case_categories, 
                                       url_get_cases_by_party, url_get_collection_exercise, 
                                       url_get_collection_exercise_go_live, url_get_ci,
                                       url_get_survey, url_post_add_survey, url_post_case_event_uuid,
                                       url_upload_ci, url_validate_enrolment)


url_get_surveys_list = app.config['FRONTSTAGE_API_URL'] + app.config['SURVEYS_LIST']
url_generate_eq_url = app.config['FRONTSTAGE_API_URL'] + app.config['GENERATE_EQ_URL']
url_confirm_add_organisation_survey = app.config['FRONTSTAGE_API_URL'] + app.config['CONFIRM_ADD_ORGANISATION_SURVEY']


with open('tests/test_data/surveys_list_seft.json') as json_data:
    surveys_list_seft = json.load(json_data)

with open('tests/test_data/surveys_list_eq.json') as json_data:
    surveys_list_eq = json.load(json_data)

encoded_jwt_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoicmVzcG9uZGVudCIsImFjY2Vzc190b2tlbiI6ImI5OWIyMjA" \
                    "0LWYxMDAtNDcxZS1iOTQ1LTIyN2EyNmVhNjljZCIsInJlZnJlc2hfdG9rZW4iOiIxZTQyY2E2MS02ZDBkLTQxYjMtODU2Yy0" \
                    "2YjhhMDhlYmIyZTMiLCJleHBpcmVzX2F0IjoxNzM4MTU4MzI4LjAsInBhcnR5X2lkIjoiZjk1NmU4YWUtNmUwZi00NDE0LWI" \
                    "wY2YtYTA3YzFhYTNlMzdiIn0.7W9yikGtX2gbKLclxv-dajcJ2NL0Nb_HDVqHrCrYvQE"


class TestSurveys(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie('localhost', 'authorization', 'session_key')
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
            }
        self.survey_file = dict(file=(io.BytesIO(b'my file contents'), "testfile.xlsx"))
        self.upload_error = {
            "error": {
                "data": {
                    "message": ".xlsx format"
                }
            }
        }
        self.patcher = patch('redis.StrictRedis.get', return_value=encoded_jwt_token)
        self.params = {
            "encrypted_enrolment_code": encrypted_enrolment_code
        }
        self.organisation_survey_data = {
            'survey_name': 'test_survey',
            'organisation_name': 'test_org'
        }
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @requests_mock.mock()
    def test_surveys_todo(self, mock_request):
        mock_request.get(url_get_surveys_list, json=surveys_list_seft)

        response = self.app.get('/surveys/todo')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Business Register and Employment Survey'.encode() in response.data)
        self.assertTrue('RUNAME1_COMPANY4 RUNNAME2_COMPANY4'.encode() in response.data)

    @requests_mock.mock()
    def test_surveys_history_seft(self, mock_request):
        mock_request.get(url_get_surveys_list, json=surveys_list_seft)

        response = self.app.get('/surveys/history')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Business Register and Employment Survey'.encode() in response.data)
        self.assertTrue('RUNAME1_COMPANY4 RUNNAME2_COMPANY4'.encode() in response.data)
        # Two entries in array, both SEFT. Although 1 is status Complete 2 buttons should show
        self.assertIn('ACCESS_SURVEY_BUTTON_1'.encode(), response.data)
        self.assertIn('ACCESS_SURVEY_BUTTON_2'.encode(), response.data)

    @requests_mock.mock()
    def test_surveys_history_eq(self, mock_request):
        mock_request.get(url_get_surveys_list, json=surveys_list_eq)

        response = self.app.get('/surveys/history')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Business Register and Employment Survey'.encode() in response.data)
        self.assertTrue('RUNAME1_COMPANY4 RUNNAME2_COMPANY4'.encode() in response.data)
        # Two entries in array, one is Complete one is not, so there should be 1 button only
        self.assertIn('ACCESS_SURVEY_BUTTON_1'.encode(), response.data)
        self.assertNotIn('ACCESS_SURVEY_BUTTON_2'.encode(), response.data)

    @requests_mock.mock()
    def test_surveys_todo_fail(self, mock_request):
        mock_request.get(url_get_surveys_list, status_code=500)

        response = self.app.get('/surveys/todo', follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_access_survey(self, mock_request):
        mock_request.get(url_get_case, json=case)
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_before_go_live)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_seft)

        response = self.app.get(f"/surveys/access_survey?case_id={case['id']}&ci_type=SEFT", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Business Register and Employment Survey'.encode() in response.data)
        self.assertTrue('RUNAME1_COMPANY4 RUNNAME2_COMPANY4'.encode() in response.data)

    @requests_mock.mock()
    def test_access_survey_eq(self, mock_request):
        mock_request.get(url_generate_eq_url, json={'eq_url': 'http://test-eq-url/session?token=test'})

        response = self.app.get('/surveys/access_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5&ci_type=EQ')
        self.assertEqual(response.status_code, 302)
        self.assertTrue('http://test-eq-url/session?token=test'.encode() in response.data)

    @requests_mock.mock()
    def test_access_survey_eq_forbidden(self, mock_request):
        mock_request.get(url_generate_eq_url, status_code=403)
        response = self.app.get('/surveys/access_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5&ci_type=EQ', follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_access_survey_title(self, mock_request):
        mock_request.get(url_get_case, json=case)
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_before_go_live)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_seft)

        response = self.app.get(f"/surveys/access_survey?case_id={case['id']}&ci_type=SEFT", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        title = f"{survey['longName']} {collection_exercise['userDescription']} - ONS Business Surveys"
        self.assertTrue(title.encode() in response.data, title)

    @requests_mock.mock()
    def test_access_survey_fail(self, mock_request):
        mock_request.get(url_get_case, status_code=500)

        response = self.app.get(f"/surveys/access_survey?case_id={case['id']}&ci_type=SEFT", follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_download_survey(self, mock_request):
        mock_request.get(url_get_case, json=case)
        mock_request.get(url_download_ci)
        mock_request.get(url_get_case_categories, json=categories)
        mock_request.post(url_post_case_event_uuid, status_code=201)

        response = self.app.get(f"/surveys/download_survey?case_id={case['id']}", follow_redirects=True)

        self.assertEqual(response.status_code, 200)

    @requests_mock.mock()
    def test_download_survey_connection_error(self, mock_request):
        mock_request.get(url_get_case, json=case)
        mock_request.get(url_get_case_categories, json=categories)
        mock_request.post(url_post_case_event_uuid, status_code=201)
        mock_request.get(url_download_ci, exc=requests.exceptions.ConnectionError(request=flask.request))

        response = self.app.get(f"/surveys/download_survey?case_id={case['id']}", follow_redirects=True)

        self.assertEqual(response.status_code, 500)

    @requests_mock.mock()
    def test_download_survey_not_found(self, mock_request):
        mock_request.get(url_get_case, json=case)
        mock_request.get(url_get_case_categories, json=categories)
        mock_request.post(url_post_case_event_uuid, status_code=201)
        mock_request.get(url_download_ci, status_code=404)

        response = self.app.get(f"/surveys/download_survey?case_id={case['id']}", follow_redirects=True)

        # NB: a non-200 response from a service will result in a 500 page displayed
        self.assertEqual(response.status_code, 500)

    @requests_mock.mock()
    def test_download_survey_fail(self, mock_request):
        mock_request.get(url_get_case, json=case)
        mock_request.get(url_get_case_categories, json=categories)
        mock_request.post(url_post_case_event_uuid, status_code=201)
        mock_request.get(url_download_ci, status_code=500)

        response = self.app.get(f"/surveys/download_survey?case_id={case['id']}", follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey(self, mock_request):
        mock_request.get(url_get_case, json=case)
        mock_request.post(url_upload_ci)
        mock_request.get(url_get_case_categories, json=categories)
        mock_request.post(url_post_case_event_uuid, status_code=201)

        test_url = f"/surveys/upload_survey?case_id={case['id']}"
        response = self.app.post(test_url, data=self.survey_file, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

    @requests_mock.mock()
    def test_upload_survey_type_error(self, mock_request):
        mock_request.post(url_upload_ci, status_code=400, json=self.upload_error)
        mock_request.get(url_get_case, status_code=200, json=case)
        mock_request.get(url_get_case_categories, json=categories)
        mock_request.post(url_post_case_event_uuid, status_code=201)
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_before_go_live)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_seft)

        test_url = f"/surveys/upload_survey?case_id={case['id']}&survey_name=Survey+Name"
        response = self.app.post(test_url, data=self.survey_file, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Error uploading - incorrect file type'.encode() in response.data)
        self.assertTrue('The spreadsheet must be in .xls or .xlsx format'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_name_length_error(self, mock_request):
        self.upload_error['error']['data']['message'] = '50 characters'
        mock_request.post(url_upload_ci, status_code=400, json=self.upload_error)
        mock_request.get(url_get_case, status_code=200, json=case)
        mock_request.get(url_get_case_categories, json=categories)
        mock_request.post(url_post_case_event_uuid, status_code=201)
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_before_go_live)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_seft)

        test_url = f"/surveys/upload_survey?case_id={case['id']}&survey_name=Survey+Name"
        response = self.app.post(test_url, data=self.survey_file, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Error uploading - file name too long'.encode() in response.data)
        self.assertTrue('The file name of your spreadsheet must be less than 50 characters long'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_file_size_error_internal(self, mock_request):
        file_data = 'a' * 21 * 1024 * 1024
        over_size_file = dict(file=(io.BytesIO(file_data.encode()), "testfile.xlsx"))
        mock_request.get(url_get_case, status_code=200, json=case)
        mock_request.get(url_get_case_categories, json=categories)
        mock_request.post(url_post_case_event_uuid, status_code=201)
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_before_go_live)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_seft)

        test_url = f"/surveys/upload_survey?case_id={case['id']}&survey_name=Survey+Name"
        response = self.app.post(test_url, data=over_size_file, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Error uploading - file size too large'.encode() in response.data)
        self.assertTrue('The spreadsheet must be smaller than 20MB in size'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_file_size_error_external(self, mock_request):
        self.upload_error['error']['data']['message'] = 'File too large'
        mock_request.post(url_upload_ci, status_code=400, json=self.upload_error)
        mock_request.get(url_get_case, status_code=200, json=case)
        mock_request.get(url_get_case_categories, json=categories)
        mock_request.post(url_post_case_event_uuid, status_code=201)
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_before_go_live)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_seft)

        test_url = f"/surveys/upload_survey?case_id={case['id']}&survey_name=Survey+Name"
        response = self.app.post(test_url, data=self.survey_file, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Error uploading - file size too large'.encode() in response.data)
        self.assertTrue('The spreadsheet must be smaller than 20MB in size'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_other_400(self, mock_request):
        self.upload_error['error']['data']['message'] = 'Random message'
        mock_request.post(url_upload_ci, status_code=400, json=self.upload_error)
        mock_request.get(url_get_case, status_code=200, json=case)
        mock_request.get(url_get_case_categories, json=categories)
        mock_request.post(url_post_case_event_uuid, status_code=201)
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_before_go_live)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_seft)

        test_url = f"/surveys/upload_survey?case_id={case['id']}&survey_name=Survey+Name"
        response = self.app.post(test_url, data=self.survey_file, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Something went wrong'.encode() in response.data)
        self.assertTrue('Please try uploading your spreadsheet again'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_fail(self, mock_request):
        mock_request.post(url_upload_ci, status_code=500)

        test_url = f"/surveys/upload_survey?case_id={case['id']}"
        response = self.app.post(test_url, data=self.survey_file, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    def test_view_add_survey_code_page(self):
        response = self.app.get('/surveys/add-survey')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Add a survey'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_add_survey_code_success(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})

        response = self.app.post('/surveys/add-survey', data={'enrolment_code': enrolment_code})

        # Check that we redirect to the confirm-organisation-survey page
        self.assertEqual(response.status_code, 302)
        self.assertTrue('confirm-organisation-survey'.encode() in response.data)

    def test_enter_add_survey_no_enrolment_code(self):
        response = self.app.post('/surveys/add-survey')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Add a survey'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_add_survey_bad_code_length(self, mock_object):
        response = self.app.post('/surveys/add-survey', data={'enrolment_code': '123'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Enrolment code not valid'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_add_survey_inactive_code(self, mock_object):
        mock_object.get(url_validate_enrolment, status_code=401, json={'active': False})

        response = self.app.post('/surveys/add-survey', data={'enrolment_code': enrolment_code})

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Enrolment code not valid'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_add_survey_invalid_code(self, mock_object):
        mock_object.get(url_validate_enrolment, status_code=404)

        response = self.app.post('/surveys/add-survey', data={'enrolment_code': enrolment_code})

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Enrolment code not valid'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_add_survey_code_fail(self, mock_object):
        mock_object.get(url_validate_enrolment, status_code=500)

        response = self.app.post('/surveys/add-survey', data={'enrolment_code': enrolment_code}, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_add_survey_used_code(self, mock_object):
        mock_object.get(url_validate_enrolment, status_code=400)

        response = self.app.post('/surveys/add-survey', data={'enrolment_code': enrolment_code}, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Enrolment code not valid'.encode() in response.data)

    @requests_mock.mock()
    def test_add_survey_confirm_org_page(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, json=case)
        mock_object.get(url_get_business_party, json=business_party)
        mock_object.get(url_get_collection_exercise, json=collection_exercise)
        mock_object.get(url_get_survey, json=survey)

        response = self.app.get('/surveys/add-survey/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Confirm organisation'.encode() in response.data)

    @requests_mock.mock()
    def test_add_survey_confirm_org_page_fail(self, mock_object):
        mock_object.post(url_confirm_add_organisation_survey, status_code=500)

        response = self.app.get('/surveys/add-survey/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_add_survey_confirm_org_page_validation_fail(self, mock_object):
        mock_object.get(url_validate_enrolment, status_code=401, json={'active': False, 'caseId': case['id']})

        response = self.app.get('/surveys/add-survey/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_add_survey_confirm_org_page_case_fail(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, status_code=500)

        response = self.app.get('/surveys/add-survey/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_add_survey_confirm_org_page_case_empty(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, json={})

        response = self.app.get('/surveys/add-survey/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_add_survey_confirm_org_page_party_fail(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, json=case)
        mock_object.get(url_get_business_party, status_code=500)

        response = self.app.get('/surveys/add-survey/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_add_survey_confirm_org_page_collex_fail(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, json=case)
        mock_object.get(url_get_business_party, json=business_party)
        mock_object.get(url_get_collection_exercise, status_code=500)

        response = self.app.get('/surveys/add-survey/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_add_survey_confirm_org_page_collex_empty(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, json=case)
        mock_object.get(url_get_business_party, json=business_party)
        mock_object.get(url_get_collection_exercise, json={})

        response = self.app.get('/surveys/add-survey/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_add_survey_confirm_org_page_survey_fail(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, json=case)
        mock_object.get(url_get_business_party, json=business_party)
        mock_object.get(url_get_collection_exercise, json=collection_exercise)
        mock_object.get(url_get_survey, status_code=500)

        response = self.app.get('/surveys/add-survey/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_add_survey_confirm_org_page_survey_empty(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, json=case)
        mock_object.get(url_get_business_party, json=business_party)
        mock_object.get(url_get_collection_exercise, json=collection_exercise)
        mock_object.get(url_get_survey, json={})

        response = self.app.get('/surveys/add-survey/confirm-organisation-survey',
                                query_string=self.params,
                                headers=self.headers,
                                follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Confirm organisation'.encode() in response.data)

    @requests_mock.mock()
    def test_add_survey_submit(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, json=case)
        mock_object.get(url_get_cases_by_party, json=[case])
        mock_object.get(url_get_case_categories, json=categories)
        mock_object.post(url_post_case_event_uuid, status_code=201)
        mock_object.post(url_post_add_survey, status_code=201)
        mock_object.get(url_get_surveys_list, json=surveys_list_seft)

        response = self.app.get('/surveys/add-survey/add-survey-submit',
                                query_string=self.params, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Business Register and Employment Survey'.encode() in response.data)
        self.assertTrue('RUNAME1_COMPANY4 RUNNAME2_COMPANY4'.encode() in response.data)

    @requests_mock.mock()
    def test_add_survey_validation_failure(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': False, 'caseId': case['id']})

        response = self.app.get('/surveys/add-survey/add-survey-submit',
                                query_string=self.params, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_add_survey_iac_error(self, mock_object):
        mock_object.get(url_validate_enrolment, status_code=500)

        response = self.app.get('/surveys/add-survey/add-survey-submit',
                                query_string=self.params, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_add_survey_get_case_error(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, status_code=500)

        response = self.app.get('/surveys/add-survey/add-survey-submit',
                                query_string=self.params, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_add_survey_post_case_error(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, json=case)
        mock_object.post(url_post_case_event_uuid, status_code=500)

        response = self.app.get('/surveys/add-survey/add-survey-submit',
                                query_string=self.params, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_add_survey_post_party_error(self, mock_object):
        mock_object.get(url_validate_enrolment, json={'active': True, 'caseId': case['id']})
        mock_object.get(url_get_case_by_enrolment_code, json=case)
        mock_object.post(url_post_case_event_uuid, status_code=201)
        mock_object.post(url_post_add_survey, status_code=500)

        response = self.app.get('/surveys/add-survey/add-survey-submit',
                                query_string=self.params, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)
