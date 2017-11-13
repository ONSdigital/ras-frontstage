import io
import json
import unittest

import requests_mock

from frontstage import app


url_get_surveys_list = app.config['RAS_FRONTSTAGE_API_SERVICE'] + 'surveys-list'
url_access_case = app.config['RAS_FRONTSTAGE_API_SERVICE'] + 'access-case'
url_download_ci = app.config['RAS_FRONTSTAGE_API_SERVICE'] + 'download-ci'
url_upload_ci = app.config['RAS_FRONTSTAGE_API_SERVICE'] + 'upload-ci'

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
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)
        self.survey_file = dict(file=(io.BytesIO(b'my file contents'), "testfile.xlsx"))
        self.upload_error = {
            "error": {
                "data": {
                    "message": ".xlsx format"
                }
            }
        }

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

    @requests_mock.mock()
    def test_upload_survey_file_size_error(self, mock_request):
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
