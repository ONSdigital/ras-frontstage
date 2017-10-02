import io
import json
import unittest

import requests_mock

from frontstage import app


with open("tests/test_data/cases.json") as json_data:
    cases_data = json.load(json_data)
with open("tests/test_data/cases_todo.json") as json_data:
    case_todo_data = json.load(json_data)
with open("tests/test_data/cases_history.json") as json_data:
    case_history_data = json.load(json_data)
with open("tests/test_data/collection_exercise.json") as json_data:
    collection_exercise_data = json.load(json_data)
with open("tests/test_data/business_party.json") as json_data:
    business_party_data = json.load(json_data)
with open("tests/test_data/survey.json") as json_data:
    survey_data = json.load(json_data)
with open('tests/test_data/collection_instrument.json') as json_data:
    collection_instrument_data = json.load(json_data)


with open('tests/test_data/case_categories.json') as json_data:
    categories_data = json.load(json_data)
with open('tests/test_data/my_party.json') as json_data:
    my_party_data = json.load(json_data)


returned_token = {
    "id": 6,
    "access_token": "a712f0f9-d00d-447a-b143-49984ca3db68",
    "expires_in": 3600,
    "token_type": "Bearer",
    "scope": "",
    "refresh_token": "37ca04d2-6b6c-4854-8e85-f59c2cc7d3de",
    "party_id": "db036fd7-ce17-40c2-a8fc-932e7c228397"

}

access_survey_form = {
    "business": "Bolts and Ratchets Ltd",
    "case_id": "ba2465b7-442a-41f6-942a-1efe3dcbdeec",
    "collection_instrument_id": "40c7c047-4fb3-4abe-926e-bf19fa2c0a1e",
    "survey": "Business Register and Employment Survey"
}

case_id = '7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb'
collection_instrument_id = '40c7c047-4fb3-4abe-926e-bf19fa2c0a1e'
party_id = "db036fd7-ce17-40c2-a8fc-932e7c228397"
encoded_jwt_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZWZyZXNoX3Rva2VuIjoiNmY5NjM0ZGEtYTI3ZS00ZDk3LWJhZjktNjN" \
                    "jOGRjY2IyN2M2IiwiYWNjZXNzX3Rva2VuIjoiMjUwMDM4YzUtM2QxOS00OGVkLThlZWMtODFmNTQyMDRjNDE1Iiwic2NvcGU" \
                    "iOlsiIl0sImV4cGlyZXNfYXQiOjE4OTM0NTk2NjEuMCwidXNlcm5hbWUiOiJ0ZXN0dXNlckBlbWFpbC5jb20iLCJyb2xlIjo" \
                    "icmVzcG9uZGVudCIsInBhcnR5X2lkIjoiZGIwMzZmZDctY2UxNy00MGMyLWE4ZmMtOTMyZTdjMjI4Mzk3In0.hh9sFpiPA-O" \
                    "8kugpDi3_GSDnxWh5rz2e5GQuBx7kmLM"

survey_file = dict(file=(io.BytesIO(b'my file contents'), "testfile.xlsx"))

url_get_case_by_party = app.config['RM_CASE_GET_BY_PARTY'].format(app.config['RM_CASE_SERVICE'], party_id, "caseevents=true")
url_get_case = app.config['RM_CASE_GET'].format(app.config['RM_CASE_SERVICE'], '7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb')
url_get_collection_exercise = app.config['RM_COLLECTION_EXERCISES_GET'].format(app.config['RM_COLLECTION_EXERCISE_SERVICE'], '14fb3e68-4dca-46db-bf49-04b84e07e77c')
url_get_business_party = app.config['RAS_PARTY_GET_BY_BUSINESS'].format(app.config['RAS_PARTY_SERVICE'], '1f5e1d68-2a4c-4698-8086-e23c0b98923f')
url_get_survey = app.config['RM_SURVEY_GET'].format(app.config['RM_SURVEY_SERVICE'], 'cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87')
url_get_ci_size = app.config['RAS_CI_SIZE'].format(app.config['RAS_COLLECTION_INSTRUMENT_SERVICE'], 'b8aad5b2-e8c3-4f48-b102-f71f310af149')
url_get_collection_instrument = app.config['RAS_CI_GET'].format(app.config['RAS_COLLECTION_INSTRUMENT_SERVICE'],
                                                                collection_instrument_id)
url_ci_download = app.config['RAS_CI_DOWNLOAD'].format(app.config['RAS_COLLECTION_INSTRUMENT_SERVICE'],
                                                       collection_instrument_id)
url_case_post = '{}cases/{}/events'.format(app.config['RM_CASE_SERVICE'], case_id)
url_case_categories = '{}categories'.format(app.config['RM_CASE_SERVICE'])
url_survey_upload = app.config['RAS_CI_UPLOAD'].format(app.config['RAS_COLLECTION_INSTRUMENT_SERVICE'], case_id)

FILE_EXTENSION_ERROR = 'The spreadsheet must be in .xls or .xlsx format'
FILE_NAME_LENGTH_ERROR = 'The file name of your spreadsheet must be less than 50 characters long'
FILE_SIZE_ERROR = 'The spreadsheet must be smaller than 20MB in size'


class TestSurveys(unittest.TestCase):
    """Test case for application endpoints and functionality"""

    def setUp(self):

        self.app = app.test_client()
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)
        self.cases_data = cases_data
        self.survey_file = dict(file=(io.BytesIO(b'my file contents'), "testfile.xlsx"))
        self.headers = {
            "Authorization": encoded_jwt_token
            }

    @requests_mock.mock()
    def test_get_surveys_todo(self, mock_object):
        mock_object.get(url_get_case_by_party, status_code=200, json=case_todo_data)
        mock_object.get(url_get_collection_exercise, status_code=200, json=collection_exercise_data)
        mock_object.get(url_get_business_party, status_code=200, json=business_party_data)
        mock_object.get(url_get_survey, status_code=200, json=survey_data)

        response = self.app.get('/surveys/', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('To do'.encode() in response.data)
        self.assertTrue('Business Register and Employment Survey'.encode() in response.data)

    @requests_mock.mock()
    def test_get_surveys_todo_empty(self, mock_object):
        mock_object.get(url_get_case_by_party, status_code=200, json=[])

        response = self.app.get('/surveys/', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('To do'.encode() in response.data)
        self.assertTrue('You have no surveys to complete'.encode() in response.data)

    @requests_mock.mock()
    def test_get_surveys_history(self, mock_object):
        mock_object.get(url_get_case_by_party, status_code=200, json=case_history_data)
        mock_object.get(url_get_collection_exercise, status_code=200, json=collection_exercise_data)
        mock_object.get(url_get_business_party, status_code=200, json=business_party_data)
        mock_object.get(url_get_survey, status_code=200, json=survey_data)

        response = self.app.get('/surveys/history', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('To do'.encode() in response.data)
        self.assertTrue('Business Register and Employment Survey'.encode() in response.data)

    @requests_mock.mock()
    def test_get_surveys_history_empty(self, mock_object):
        mock_object.get(url_get_case_by_party, status_code=200, json=[])

        response = self.app.get('/surveys/history', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('To do'.encode() in response.data)
        self.assertTrue('No items to show'.encode() in response.data)

    @requests_mock.mock()
    def test_view_access_surveys(self, mock_object):
        mock_object.get(url_get_case, status_code=200, json=cases_data)
        mock_object.get(url_get_collection_exercise, status_code=200, json=collection_exercise_data)
        mock_object.get(url_get_business_party, status_code=200, json=business_party_data)
        mock_object.get(url_get_survey, status_code=200, json=survey_data)
        mock_object.get(url_get_ci_size, status_code=200, json={'size': 1000})
        mock_object.get(url_get_collection_instrument, status_code=200, json=collection_instrument_data)
        self.headers['referer'] = '/surveys/access_survey'

        response = self.app.get('/surveys/access_survey?case_id={}'.format(case_id), follow_redirects=True, data=access_survey_form, headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('RUNAME1_COMPANY421'.encode() in response.data)
        self.assertTrue('Download'.encode() in response.data)

    @requests_mock.mock()
    def test_view_access_surveys_case_fail(self, mock_object):
        mock_object.get(url_get_case, status_code=500)
        self.headers['referer'] = '/surveys/access_survey'

        response = self.app.get('/surveys/access_survey?case_id={}'.format(case_id), follow_redirects=True, data=access_survey_form, headers=self.headers)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    # @requests_mock.mock()
    # def test_view_access_surveys_ci_fail(self, mock_object):
    #     mock_object.get(url_get_case, status_code=200, json=cases_data)
    #     mock_object.get(url_get_collection_instrument, status_code=500)
    #     self.headers['referer'] = '/surveys/access_survey'
    #
    #     response = self.app.get('/surveys/access_survey?case_id={}'.format(case_id), follow_redirects=True, data=access_survey_form, headers=self.headers)
    #
    #     self.assertEqual(response.status_code, 500)
    #     self.assertTrue('Server error'.encode() in response.data)
    #
    # @requests_mock.mock()
    # def test_view_access_surveys_permission_fail(self, mock_object):
    #     self.cases_data[0]['collectionInstrumentId'] = 'somethingelse'
    #     mock_object.get(url_get_case_by_party, status_code=200, json=self.cases_data)
    #     mock_object.get(url_get_collection_instrument, status_code=200, json=collection_instrument_data)
    #     self.headers['referer'] = '/surveys/access_survey'
    #
    #     response = self.app.get('/surveys/access_survey?case_id={}'.format(case_id), follow_redirects=True, data=access_survey_form, headers=self.headers)
    #
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTrue('Oops!'.encode() in response.data)

    @requests_mock.mock()
    def test_download_survey(self, mock_object):
        mock_object.get(url_get_case, status_code=200, json=cases_data)
        mock_object.get(url_ci_download, status_code=200)
        mock_object.get(url_case_categories, status_code=200, json=categories_data)
        mock_object.post(url_case_post, status_code=201)

        response = self.app.get('/surveys/download_survey?cid={}&case_id={}'.format(collection_instrument_id, case_id), follow_redirects=True)

        self.assertEqual(response.status_code, 200)

    @requests_mock.mock()
    def test_download_survey_case_fail(self, mock_object):
        mock_object.get(url_get_case, status_code=500)

        response = self.app.get('/surveys/download_survey?cid={}&case_id={}'.format(collection_instrument_id, case_id),
                                follow_redirects=True,
                                data=access_survey_form)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_download_survey_download_fail(self, mock_object):
        mock_object.get(url_get_case, status_code=200, json=cases_data)
        mock_object.get(url_ci_download, status_code=500)
        mock_object.get(url_case_categories, status_code=200, json=categories_data)
        mock_object.post(url_case_post, status_code=201)

        response = self.app.get('/surveys/download_survey?cid={}&case_id={}'.format(collection_instrument_id, case_id),
                                follow_redirects=True,
                                data=access_survey_form)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Something went wrong'.encode() in response.data)

    @requests_mock.mock()
    def test_download_survey_categories_fail(self, mock_object):
        mock_object.get(url_get_case, status_code=200, json=cases_data)
        mock_object.get(url_ci_download, status_code=200)
        mock_object.get(url_case_categories, status_code=500)
        mock_object.post(url_case_post, status_code=201)

        response = self.app.get('/surveys/download_survey?cid={}&case_id={}'.format(collection_instrument_id, case_id),
                                follow_redirects=True,
                                data=access_survey_form)

        # We don't want to stop the users journey when we fail to post case events?
        self.assertEqual(response.status_code, 200)

    @requests_mock.mock()
    def test_download_survey_case_post_fail(self, mock_object):
        mock_object.get(url_get_case, status_code=200, json=cases_data)
        mock_object.get(url_ci_download, status_code=200)
        mock_object.get(url_case_categories, status_code=200, json=categories_data)
        mock_object.post(url_case_post, status_code=500)

        response = self.app.get('/surveys/download_survey?cid={}&case_id={}'.format(collection_instrument_id, case_id),
                                follow_redirects=True,
                                data=access_survey_form)

        # We don't want to stop the users journey when we fail to post case events?
        self.assertEqual(response.status_code, 200)

    @requests_mock.mock()
    def test_upload_survey(self, mock_object):
        mock_object.get(url_get_case_by_party, status_code=200, json=case_todo_data)
        mock_object.post(url_survey_upload, status_code=200)
        mock_object.get(url_case_categories, status_code=200, json=categories_data)
        mock_object.post(url_case_post, status_code=201)

        response = self.app.post('/surveys/upload_survey?party_id={}&case_id={}'.format(party_id, case_id),
                                 content_type='multipart/form-data',
                                 follow_redirects=True,
                                 data=self.survey_file)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('File uploaded successfully'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_case_fail(self, mock_object):
        mock_object.get(url_get_case_by_party, status_code=500)

        response = self.app.post('/surveys/upload_survey?party_id={}&case_id={}'.format(party_id, case_id),
                                 content_type='multipart/form-data',
                                 follow_redirects=True,
                                 data=self.survey_file)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_upload_fail(self, mock_object):
        mock_object.get(url_get_case_by_party, status_code=200, json=case_todo_data)
        mock_object.post(url_survey_upload, status_code=500)
        mock_object.get(url_case_categories, status_code=200, json=categories_data)
        mock_object.post(url_case_post, status_code=201)

        response = self.app.post('/surveys/upload_survey?party_id={}&case_id={}'.format(party_id, case_id),
                                 content_type='multipart/form-data',
                                 follow_redirects=True,
                                 data=self.survey_file)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Something went wrong'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_upload_file_name_too_long(self, mock_object):
        mock_object.get(url_get_case_by_party, status_code=200, json=case_todo_data)
        mock_object.post(url_survey_upload, status_code=400, text=FILE_NAME_LENGTH_ERROR)
        mock_object.get(url_case_categories, status_code=200, json=categories_data)
        mock_object.post(url_case_post, status_code=201)

        response = self.app.post('/surveys/upload_survey?party_id={}&case_id={}'.format(party_id, case_id),
                                 content_type='multipart/form-data',
                                 follow_redirects=True,
                                 data=self.survey_file)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(FILE_NAME_LENGTH_ERROR.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_upload_file_extension_incorrect(self, mock_object):
        mock_object.get(url_get_case_by_party, status_code=200, json=case_todo_data)
        mock_object.post(url_survey_upload, status_code=400, text=FILE_EXTENSION_ERROR)
        mock_object.get(url_case_categories, status_code=200, json=categories_data)
        mock_object.post(url_case_post, status_code=201)

        response = self.app.post('/surveys/upload_survey?party_id={}&case_id={}'.format(party_id, case_id),
                                 content_type='multipart/form-data',
                                 follow_redirects=True,
                                 data=self.survey_file)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(FILE_EXTENSION_ERROR.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_exceeded_upload_size(self, mock_object):
        mock_object.get(url_get_case_by_party, status_code=200, json=case_todo_data)
        mock_object.post(url_survey_upload, status_code=200)
        mock_object.get(url_case_categories, status_code=200, json=categories_data)
        mock_object.post(url_case_post, status_code=201)

        file_data = 'a' * 21 * 1024 * 1024
        over_size_file = dict(file=(io.BytesIO(file_data.encode()), "testfile.xlsx"))

        response = self.app.post('/surveys/upload_survey?party_id={}&case_id={}'.format(party_id, case_id),
                                 content_type='multipart/form-data',
                                 follow_redirects=True,
                                 data=over_size_file)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(FILE_SIZE_ERROR.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_categories_fail(self, mock_object):
        mock_object.get(url_get_case_by_party, status_code=200, json=case_todo_data)
        mock_object.post(url_survey_upload, status_code=200)
        mock_object.get(url_case_categories, status_code=500, json=categories_data)
        mock_object.post(url_case_post, status_code=201)

        response = self.app.post('/surveys/upload_survey?case_id={}'.format(case_id),
                                 content_type='multipart/form-data',
                                 follow_redirects=True,
                                 data=self.survey_file)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('File uploaded successfully'.encode() in response.data)

    @requests_mock.mock()
    def test_upload_survey_categories_fail(self, mock_object):
        mock_object.get(url_get_case_by_party, status_code=200, json=case_todo_data)
        mock_object.post(url_survey_upload, status_code=200)
        mock_object.get(url_case_categories, status_code=200, json=categories_data)
        mock_object.post(url_case_post, status_code=500)

        response = self.app.post('/surveys/upload_survey?party_id={}&case_id={}'.format(party_id, case_id),
                                 content_type='multipart/form-data',
                                 follow_redirects=True,
                                 data=self.survey_file)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('File uploaded successfully'.encode() in response.data)

    def test_upload_failed_upload_file_extension_incorrect(self):

        response = self.app.get('/surveys/upload_failed?error_info={}&case_id={}'.format('type', case_id),
                                follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(FILE_EXTENSION_ERROR.encode() in response.data)

    def test_upload_failed_upload_file_name_too_long(self):

        response = self.app.get('/surveys/upload_failed?error_info={}&case_id={}'.format('charLimit', case_id),
                                follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(FILE_NAME_LENGTH_ERROR.encode() in response.data)

    def test_upload_failed_upload_file_size_too_large(self):

        response = self.app.get('/surveys/upload_failed?error_info={}&case_id={}'.format('size', case_id),
                                follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(FILE_SIZE_ERROR.encode() in response.data)

    def test_upload_failed_unexpected_error(self):

        response = self.app.get('/surveys/upload_failed?case_id={}'.format(case_id),
                                follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(b'Please try uploading your spreadsheet again' in response.data)
