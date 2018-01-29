import io
import json
import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app


url_get_surveys_list = app.config['RAS_FRONTSTAGE_API_SERVICE'] + app.config['SURVEYS_LIST']
url_access_case = app.config['RAS_FRONTSTAGE_API_SERVICE'] + app.config['ACCESS_CASE']
url_download_ci = app.config['RAS_FRONTSTAGE_API_SERVICE'] + app.config['DOWNLOAD_CI']
url_upload_ci = app.config['RAS_FRONTSTAGE_API_SERVICE'] + app.config['UPLOAD_CI']
url_validate_enrolment = '{}{}'.format(app.config['RAS_FRONTSTAGE_API_SERVICE'], app.config['VALIDATE_ENROLMENT'])
url_confirm_add_organisation_survey = '{}{}'.format(app.config['RAS_FRONTSTAGE_API_SERVICE'],
                                                    app.config['CONFIRM_ADD_ORGANISATION_SURVEY'])

with open('tests/test_data/surveys_list.json') as json_data:
    surveys_list = json.load(json_data)

encoded_jwt_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZWZyZXNoX3Rva2VuIjoiNmY5NjM0ZGEtYTI3ZS00ZDk3LWJhZjktNjN" \
                    "jOGRjY2IyN2M2IiwiYWNjZXNzX3Rva2VuIjoiMjUwMDM4YzUtM2QxOS00OGVkLThlZWMtODFmNTQyMDRjNDE1Iiwic2NvcGU" \
                    "iOlsiIl0sImV4cGlyZXNfYXQiOjE4OTM0NTk2NjEuMCwidXNlcm5hbWUiOiJ0ZXN0dXNlckBlbWFpbC5jb20iLCJyb2xlIjo" \
                    "icmVzcG9uZGVudCIsInBhcnR5X2lkIjoiZGIwMzZmZDctY2UxNy00MGMyLWE4ZmMtOTMyZTdjMjI4Mzk3In0.hh9sFpiPA-O" \
                    "8kugpDi3_GSDnxWh5rz2e5GQuBx7kmLM"


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
    def test_surveys_todo(self, mock_request):
        mock_request.get(url_get_surveys_list, json=surveys_list)

        response = self.app.get('/surveys/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Business Register and Employment Survey'.encode() in response.data)
        self.assertTrue('RUNAME1_COMPANY4 RUNNAME2_COMPANY4'.encode() in response.data)

    @requests_mock.mock()
    def test_surveys_history(self, mock_request):
        mock_request.get(url_get_surveys_list, json=surveys_list)

        response = self.app.get('/surveys/history')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Business Register and Employment Survey'.encode() in response.data)
        self.assertTrue('RUNAME1_COMPANY4 RUNNAME2_COMPANY4'.encode() in response.data)

    @requests_mock.mock()
    def test_surveys_todo_fail(self, mock_request):
        mock_request.get(url_get_surveys_list, status_code=500)

        response = self.app.get('/surveys/', follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_access_survey(self, mock_request):
        mock_request.get(url_access_case, json=surveys_list[0])

        response = self.app.get('/surveys/access_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Business Register and Employment Survey'.encode() in response.data)
        self.assertTrue('RUNAME1_COMPANY4 RUNNAME2_COMPANY4'.encode() in response.data)

    @requests_mock.mock()
    def test_access_survey_fail(self, mock_request):
        mock_request.get(url_access_case, status_code=500)

        response = self.app.get('/surveys/access_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5', follow_redirects=True)

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

        test_url = '/surveys/upload_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5'
        response = self.app.post(test_url, data=self.survey_file, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Error uploading - incorrect file type'.encode() in response.data)
        self.assertTrue('The spreadsheet must be in .xls or .xlsx format'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_name_length_error(self, mock_request):
        self.upload_error['error']['data']['message'] = '50 characters'
        mock_request.post(url_upload_ci, status_code=400, json=self.upload_error)

        test_url = '/surveys/upload_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5'
        response = self.app.post(test_url, data=self.survey_file, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Error uploading - file name too long'.encode() in response.data)
        self.assertTrue('The file name of your spreadsheet must be less than 50 characters long'.encode() in response.data)

    def test_upload_survey_file_size_error_internal(self):
        file_data = 'a' * 21 * 1024 * 1024
        over_size_file = dict(file=(io.BytesIO(file_data.encode()), "testfile.xlsx"))

        test_url = '/surveys/upload_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5'
        response = self.app.post(test_url, data=over_size_file, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Error uploading - file size too large'.encode() in response.data)
        self.assertTrue('The spreadsheet must be smaller than 20MB in size'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_file_size_error_external(self, mock_request):
        self.upload_error['error']['data']['message'] = 'File too large'
        mock_request.post(url_upload_ci, status_code=400, json=self.upload_error)

        test_url = '/surveys/upload_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5'
        response = self.app.post(test_url, data=self.survey_file, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Error uploading - file size too large'.encode() in response.data)
        self.assertTrue('The spreadsheet must be smaller than 20MB in size'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_other_400(self, mock_request):
        self.upload_error['error']['data']['message'] = 'Random message'
        mock_request.post(url_upload_ci, status_code=400, json=self.upload_error)

        test_url = '/surveys/upload_survey?case_id=b2457bd4-004d-42d1-a1c6-a514973d9ae5'
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
        response = self.app.get('/register/create-account')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Create an account'.encode() in response.data)
        self.assertTrue('Enrolment Code'.encode() in response.data)

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

        response = self.app.post('/surveys/add-survey', data={'enrolment_code': 'test_enrolment'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Enrolment code not valid'.encode() in response.data)

    @requests_mock.mock()
    def test_enter_add_survey_invalid_code(self, mock_object):
        mock_object.post(url_validate_enrolment, status_code=404)

        response = self.app.post('/surveys/add-survey', data={'enrolment_code': '123456789012'})

        self.assertEqual(response.status_code, 202)
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
