import io
import logging
import unittest
from unittest.mock import patch

from requests.models import Response
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import CiUploadError
from tests.app.mocked_services import business_party, case, encoded_jwt_token, survey, url_upload_ci

logger = wrap_logger(logging.getLogger(__name__))


class TestUploadSurvey(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie('localhost', 'authorization', 'session_key')
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
            }
        self.survey_file = dict(file=(io.BytesIO(b'my file contents'), "testfile.xlsx"))
        self.patcher = patch('redis.StrictRedis.get', return_value=encoded_jwt_token)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @patch('frontstage.controllers.collection_instrument_controller.upload_collection_instrument')
    @patch('frontstage.controllers.party_controller.is_respondent_enrolled')
    def test_upload_survey_success(self, *_):
        urls = ['upload_survey', 'upload-survey']
        for url in urls:
            with self.subTest(url=url):
                self.survey_file = dict(file=(io.BytesIO(b'my file contents'), "testfile.xlsx"))
                response = self.app.post(f'/surveys/{url}?case_id={case["id"]}&business_party_id={business_party["id"]}'
                                         f'&survey_short_name={survey["shortName"]}', data=self.survey_file)

                self.assertEqual(response.status_code, 200)

    @patch('frontstage.controllers.collection_instrument_controller.upload_collection_instrument')
    @patch('frontstage.controllers.party_controller.is_respondent_enrolled')
    def test_upload_survey_fail_unexpected_error(self, _, upload_ci):
        error_response = Response()
        error_response.status_code = 500
        error_response.url = url_upload_ci
        error_message = "fail"
        error = CiUploadError(logger, error_response, error_message)
        upload_ci.side_effect = error
        urls = ['upload_survey', 'upload-survey']
        for url in urls:
            with self.subTest(url=url):
                self.survey_file = dict(file=(io.BytesIO(b'my file contents'), "testfile.xlsx"))
                response = self.app.post(f'/surveys/{url}?case_id={case["id"]}&business_party_id={business_party["id"]}'
                                         f'&survey_short_name={survey["shortName"]}', data=self.survey_file)

                self.assertEqual(response.status_code, 302)
                self.assertTrue('/surveys/upload-failed'.encode() in response.data)

    @patch('frontstage.controllers.collection_instrument_controller.upload_collection_instrument')
    @patch('frontstage.controllers.party_controller.is_respondent_enrolled')
    def test_upload_survey_fail_type_error(self, _, upload_ci):
        error_response = Response()
        error_response.status_code = 500
        error_response.url = url_upload_ci
        error_message = ".xlsx format"
        error = CiUploadError(logger, error_response, error_message)
        upload_ci.side_effect = error
        urls = ['upload_survey', 'upload-survey']
        for url in urls:
            with self.subTest(url=url):
                self.survey_file = dict(file=(io.BytesIO(b'my file contents'), "testfile.xlsx"))
                response = self.app.post(f'/surveys/{url}?case_id={case["id"]}&business_party_id={business_party["id"]}'
                                         f'&survey_short_name={survey["shortName"]}', data=self.survey_file)

                self.assertEqual(response.status_code, 302)
                self.assertTrue('/surveys/upload-failed'.encode() in response.data)

    @patch('frontstage.controllers.collection_instrument_controller.upload_collection_instrument')
    @patch('frontstage.controllers.party_controller.is_respondent_enrolled')
    def test_upload_survey_fail_char_limit_error(self, _, upload_ci):
        error_response = Response()
        error_response.status_code = 500
        error_response.url = url_upload_ci
        error_message = "50 characters"
        error = CiUploadError(logger, error_response, error_message)
        upload_ci.side_effect = error
        urls = ['upload_survey', 'upload-survey']
        for url in urls:
            with self.subTest(url=url):
                self.survey_file = dict(file=(io.BytesIO(b'my file contents'), "testfile.xlsx"))
                response = self.app.post(f'/surveys/{url}?case_id={case["id"]}&business_party_id={business_party["id"]}'
                                         f'&survey_short_name={survey["shortName"]}', data=self.survey_file)

                self.assertEqual(response.status_code, 302)
                self.assertTrue('/surveys/upload-failed'.encode() in response.data)

    @patch('frontstage.controllers.collection_instrument_controller.upload_collection_instrument')
    @patch('frontstage.controllers.party_controller.is_respondent_enrolled')
    def test_upload_survey_fail_size_error(self, _, upload_ci):
        error_response = Response()
        error_response.status_code = 500
        error_response.url = url_upload_ci
        error_message = "File too large"
        error = CiUploadError(logger, error_response, error_message)
        upload_ci.side_effect = error

        urls = ['upload-survey', 'upload_survey']
        for url in urls:
            with self.subTest(url=url):
                self.survey_file = dict(file=(io.BytesIO(b'my file contents'), "testfile.xlsx"))
                response = self.app.post(f'/surveys/{url}?case_id={case["id"]}&business_party_id={business_party["id"]}'
                                         f'&survey_short_name={survey["shortName"]}', data=self.survey_file)

                self.assertEqual(response.status_code, 302)
                self.assertTrue('/surveys/upload-failed'.encode() in response.data)

    def test_upload_survey_content_too_long(self):
        file_data = 'a' * 21 * 1024 * 1024
        urls = ['upload_survey', 'upload-survey']
        for url in urls:
            with self.subTest(url=url):
                over_size_file = dict(file=(io.BytesIO(file_data.encode()), "testfile.xlsx"))
                response = self.app.post(f'/surveys/{url}?case_id={case["id"]}&business_party_id={business_party["id"]}'
                                         f'&survey_short_name={survey["shortName"]}', data=over_size_file)

                self.assertEqual(response.status_code, 302)
                self.assertTrue('/surveys/upload-failed'.encode() in response.data)
