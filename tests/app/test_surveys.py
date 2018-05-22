import io
import json
import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from tests.app.mocked_services import (business_party, business_party_no_trading_as,
                                       case, collection_exercise, completed_case, completed_by_phone_case,
                                       collection_exercise_go_live_event, collection_exercise_go_live_event_before,
                                       collection_exercise_before_go_live, collection_instrument_seft, survey,
                                       url_get_cases_by_party, url_get_business_party,
                                       url_get_collection_exercise, url_get_collection_exercise_go_live,
                                       url_get_ci, url_get_survey)

url_access_case = app.config['RAS_FRONTSTAGE_API_SERVICE'] + app.config['ACCESS_CASE']
url_generate_eq_url = app.config['RAS_FRONTSTAGE_API_SERVICE'] + app.config['GENERATE_EQ_URL']
url_download_ci = app.config['RAS_FRONTSTAGE_API_SERVICE'] + app.config['DOWNLOAD_CI']
url_upload_ci = app.config['RAS_FRONTSTAGE_API_SERVICE'] + app.config['UPLOAD_CI']
url_validate_enrolment = '{}{}'.format(app.config['RAS_FRONTSTAGE_API_SERVICE'], app.config['VALIDATE_ENROLMENT'])
url_add_survey = app.config['RAS_FRONTSTAGE_API_SERVICE'] + app.config['ADD_SURVEY']
url_confirm_add_organisation_survey = '{}{}'.format(app.config['RAS_FRONTSTAGE_API_SERVICE'],
                                                    app.config['CONFIRM_ADD_ORGANISATION_SURVEY'])

with open('tests/test_data/surveys_list_seft.json') as fp:
    surveys_list_seft = json.load(fp)

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
        self.encrypted_enrolment_code = 'WfwJghohWOZTIYnutlTcVucqnuED5Lm9q8t0L4ASHPo='
        self.params = {
            "encrypted_enrolment_code": self.encrypted_enrolment_code
        }
        self.organisation_survey_data = {
            'survey_name': 'test_survey',
            'organisation_name': 'test_org'
        }
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @requests_mock.mock()
    def test_get_surveys_list_todo(self, mock_request):
        mock_request.get(url_get_cases_by_party, json=[case])
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_go_live_event)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_seft)

        response = self.app.get('/surveys/todo', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Surveys to complete'.encode(), response.data)

    @requests_mock.mock()
    def test_surveys_todo_trading_as(self, mock_request):
        mock_request.get(url_get_cases_by_party, json=[case])
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_go_live_event)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_seft)

        response = self.app.get('/surveys/todo', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('PC Company'.encode(), response.data)

    @requests_mock.mock()
    def test_surveys_todo_no_trading_as(self, mock_request):
        mock_request.get(url_get_cases_by_party, json=[case])
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_go_live_event)
        mock_request.get(url_get_business_party, json=business_party_no_trading_as)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_seft)

        response = self.app.get('/surveys/todo')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('PC Company'.encode(), response.data)

    @requests_mock.mock()
    def test_surveys_history_trading_as(self, mock_request):
        mock_request.get(url_get_cases_by_party, json=[completed_case])
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_go_live_event)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_seft)

        response = self.app.get('/surveys/history')

        self.assertEqual(response.status_code, 200)
        self.assertIn('PC Company'.encode(), response.data)

    @requests_mock.mock()
    def test_surveys_history_no_trading_as(self, mock_request):
        mock_request.get(url_get_cases_by_party, json=[case])
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_go_live_event)
        mock_request.get(url_get_business_party, json=business_party_no_trading_as)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_seft)

        response = self.app.get('/surveys/history')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('PC Company'.encode(), response.data)

    @requests_mock.mock()
    def test_surveys_history_seft(self, mock_request):
        mock_request.get(url_get_cases_by_party, json=[case])
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_go_live_event)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_seft)

        response = self.app.get('/surveys/history', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Completed surveys'.encode(), response.data)

    @requests_mock.mock()
    def test_get_surveys_list_todo_before_go_live(self, mock_request):
        mock_request.get(url_get_cases_by_party, json=[case])
        mock_request.get(url_get_collection_exercise, json=collection_exercise_before_go_live)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_go_live_event_before)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_seft)

        response = self.app.get('/surveys/todo', follow_redirects=True)

        self.assertEqual(response.status_code, 200)

    @requests_mock.mock()
    def test_get_surveys_list_history(self, mock_request):
        mock_request.get(url_get_cases_by_party, json=[completed_case])
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_go_live_event)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_seft)

        response = self.app.get('/surveys/todo', follow_redirects=True)

        self.assertEqual(response.status_code, 200)

    @requests_mock.mock()
    def test_get_surveys_list_history_includes_completed_by_phone(self, mock_request):
        mock_request.get(url_get_cases_by_party, json=completed_by_phone_case)
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_go_live_event)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, json=collection_instrument_seft)

        response = self.app.get('/surveys/todo', follow_redirects=True)

        self.assertEqual(response.status_code, 200)

    @requests_mock.mock()
    def test_get_surveys_list_todo_case_fail(self, mock_request):
        mock_request.get(url_get_cases_by_party, status_code=500)

        response = self.app.get('/surveys/todo', follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_get_surveys_list_todo_collection_exercise_fail(self, mock_request):
        mock_request.get(url_get_cases_by_party, json=[case])
        mock_request.get(url_get_collection_exercise, status_code=500)

        response = self.app.get('/surveys/todo', follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_get_surveys_list_todo_collection_exercise_event_fail(self, mock_request):
        mock_request.get(url_get_cases_by_party, json=[case])
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, status_code=500)

        response = self.app.get('/surveys/todo', follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_get_surveys_list_todo_party_fail(self, mock_request):
        mock_request.get(url_get_cases_by_party, json=[case])
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_go_live_event)
        mock_request.get(url_get_business_party, status_code=500)

        response = self.app.get('/surveys/todo', follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_get_surveys_list_todo_survey_fail(self, mock_request):
        mock_request.get(url_get_cases_by_party, json=[case])
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_go_live_event)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, status_code=500)

        response = self.app.get('/surveys/todo', follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_get_surveys_list_todo_collection_instrument_fail(self, mock_request):
        mock_request.get(url_get_cases_by_party, json=[case])
        mock_request.get(url_get_collection_exercise, json=collection_exercise)
        mock_request.get(url_get_collection_exercise_go_live, json=collection_exercise_go_live_event)
        mock_request.get(url_get_business_party, json=business_party)
        mock_request.get(url_get_survey, json=survey)
        mock_request.get(url_get_ci, status_code=500)

        response = self.app.get('/surveys/todo', follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_access_survey(self, mock_request):
        mock_request.get(url_access_case, json=surveys_list_seft[0])

        response = self.app.get('/surveys/access_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5&ci_type=SEFT', follow_redirects=True)

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
        mock_request.get(url_access_case, json=surveys_list_seft[1])

        response = self.app.get('/surveys/access_survey?case_id=t3577bd4-004d-42d1-a1c6-a514973d9ae5&ci_type=SEFT', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Test Survey December 2017 - ONS Business Surveys'.encode() in response.data)

    @requests_mock.mock()
    def test_access_survey_fail(self, mock_request):
        mock_request.get(url_access_case, status_code=500)

        response = self.app.get('/surveys/access_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5&ci_type=SEFT', follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_download_survey(self, mock_request):
        mock_request.get(url_download_ci)

        response = self.app.get('/surveys/download_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5', follow_redirects=True)

        self.assertEqual(response.status_code, 200)

    @requests_mock.mock()
    def test_download_survey_fail(self, mock_request):
        mock_request.get(url_download_ci, status_code=500)

        response = self.app.get('/surveys/download_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5', follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey(self, mock_request):
        mock_request.post(url_upload_ci)

        test_url = '/surveys/upload_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5'
        response = self.app.post(test_url, data=self.survey_file, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

    @requests_mock.mock()
    def test_upload_survey_type_error(self, mock_request):
        mock_request.post(url_upload_ci, status_code=400, json=self.upload_error)
        mock_request.get(url_access_case, status_code=200, json=surveys_list_seft[1])

        test_url = '/surveys/upload_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5&survey_name=Survey+Name'
        response = self.app.post(test_url, data=self.survey_file, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Error uploading - incorrect file type'.encode() in response.data)
        self.assertTrue('The spreadsheet must be in .xls or .xlsx format'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_name_length_error(self, mock_request):
        self.upload_error['error']['data']['message'] = '50 characters'
        mock_request.post(url_upload_ci, status_code=400, json=self.upload_error)
        mock_request.get(url_access_case, status_code=200, json=surveys_list_seft[1])

        test_url = '/surveys/upload_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5&survey_name=Survey+Name'
        response = self.app.post(test_url, data=self.survey_file, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Error uploading - file name too long'.encode() in response.data)
        self.assertTrue('The file name of your spreadsheet must be less than 50 characters long'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_file_size_error_internal(self, mock_request):
        file_data = 'a' * 21 * 1024 * 1024
        over_size_file = dict(file=(io.BytesIO(file_data.encode()), "testfile.xlsx"))
        mock_request.get(url_access_case, status_code=200, json=surveys_list_seft[1])
        test_url = '/surveys/upload_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5&survey_name=Survey+Name'
        response = self.app.post(test_url, data=over_size_file, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Error uploading - file size too large'.encode() in response.data)
        self.assertTrue('The spreadsheet must be smaller than 20MB in size'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_file_size_error_external(self, mock_request):
        self.upload_error['error']['data']['message'] = 'File too large'
        mock_request.post(url_upload_ci, status_code=400, json=self.upload_error)
        mock_request.get(url_access_case, status_code=200, json=surveys_list_seft[1])

        test_url = '/surveys/upload_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5&survey_name=Survey+Name'
        response = self.app.post(test_url, data=self.survey_file, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Error uploading - file size too large'.encode() in response.data)
        self.assertTrue('The spreadsheet must be smaller than 20MB in size'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_other_400(self, mock_request):
        self.upload_error['error']['data']['message'] = 'Random message'
        mock_request.post(url_upload_ci, status_code=400, json=self.upload_error)
        mock_request.get(url_access_case, status_code=200, json=surveys_list_seft[1])
        test_url = '/surveys/upload_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5&survey_name=Survey+Name'
        response = self.app.post(test_url, data=self.survey_file, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Something went wrong'.encode() in response.data)
        self.assertTrue('Please try uploading your spreadsheet again'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_fail(self, mock_request):
        mock_request.post(url_upload_ci, status_code=500)

        test_url = '/surveys/upload_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5'
        response = self.app.post(test_url, data=self.survey_file, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    def test_view_add_survey_code_page(self):
        response = self.app.get('/surveys/add-survey')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Add a survey'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_add_survey_code_success(self, mock_object):
        mock_object.post(url_validate_enrolment)

        response = self.app.post('/surveys/add-survey', data={'enrolment_code': '123456789012'})

        # Check that we redirect to the confirm-organisation-survey page
        self.assertEqual(response.status_code, 302)
        self.assertTrue('confirm-organisation-survey'.encode() in response.data)

    def test_enter_add_survey_no_enrolment_code(self):
        response = self.app.post('/surveys/add-survey')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Add a survey'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_add_survey_inactive_code(self, mock_object):
        mock_object.post(url_validate_enrolment, status_code=401, json={'active': False})

        response = self.app.post('/surveys/add-survey', data={'enrolment_code': '123456789012'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Enrolment code not valid'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_add_survey_invalid_code(self, mock_object):
        mock_object.post(url_validate_enrolment, status_code=404)

        response = self.app.post('/surveys/add-survey', data={'enrolment_code': '123456789012'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Enrolment code not valid'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_add_survey_code_fail(self, mock_object):
        mock_object.post(url_validate_enrolment, status_code=500)

        response = self.app.post('/surveys/add-survey', data={'enrolment_code': '123456789012'}, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_add_survey_used_code(self, mock_object):
        mock_object.post(url_validate_enrolment, status_code=400)

        response = self.app.post('/surveys/add-survey', data={'enrolment_code': '123456789012'}, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Enrolment code not valid'.encode() in response.data)

    @requests_mock.mock()
    def test_add_survey_confirm_org_page(self, mock_object):
        mock_object.post(url_confirm_add_organisation_survey, status_code=200, json=self.organisation_survey_data)

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
    def test_add_survey_submit(self, mock_object):
        mock_object.post(url_add_survey, json={'case_id': "test_case_id"})

        url = '/surveys/add-survey/add-survey-submit' \
              '?encrypted_enrolment_code=WfwJghohWOZTIYnutlTcVucqnuED5Lm9q8t0L4ASHPo='
        response = self.app.get(url)

        self.assertEqual(response.status_code, 302)

    @requests_mock.mock()
    def test_add_survey_failure(self, mock_object):
        mock_object.post(url_add_survey, status_code=500)

        url = '/surveys/add-survey/add-survey-submit' \
              '?encrypted_enrolment_code=WfwJghohWOZTIYnutlTcVucqnuED5Lm9q8t0L4ASHPo='
        response = self.app.get(url, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)
