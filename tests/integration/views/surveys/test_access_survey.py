import io
import unittest
from unittest.mock import patch

from frontstage import app
from tests.integration.mocked_services import (collection_exercise, collection_instrument_seft, survey, business_party,
                                               encoded_jwt_token, encrypted_enrolment_code)


class TestAccessSurvey(unittest.TestCase):

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
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @patch('frontstage.controllers.case_controller.get_case_data')
    def test_access_survey_all_expected_case_data(self, get_case_data):
        case_data = {
            "collection_exercise": collection_exercise,
            "collection_instrument": collection_instrument_seft,
            "survey": survey,
            "business_party": business_party
        }
        get_case_data.return_value = case_data

        urls = ['access_survey', 'access-survey']
        for url in urls:
            with self.subTest(url=url):

                response = self.app.get(f'/surveys/{url}?case_id=8cdc01f9-656a-4715-a148-ffed0dbe1b04&business_party_id=0008279d-9425-4e28-897d-bfd876aa7f3f&'
                                        'survey_short_name=Bricks&ci_type=SEFT', headers=self.headers)

                self.assertEqual(response.status_code, 200)
                self.assertIn(survey['shortName'].encode(), response.data)

    @patch('frontstage.controllers.case_controller.get_case_data')
    def test_access_survey_missing_collection_intrument_from_case_data(self, get_case_data):
        case_data = {
            "collection_exercise": collection_exercise,
            "survey": survey,
            "business_party": business_party
        }
        get_case_data.return_value = case_data
        urls = ['access_survey', 'access-survey']
        for url in urls:
            with self.subTest(url=url):
                response = self.app.get(f'/surveys/{url}?case_id=8cdc01f9-656a-4715-a148-ffed0dbe1b04&business_party_id=0008279d-9425-4e28-897d-bfd876aa7f3f&'
                                        'survey_short_name=Bricks&ci_type=SEFT', headers=self.headers, follow_redirects=True)

                self.assertEqual(response.status_code, 500)
                self.assertTrue('An error has occurred'.encode() in response.data)

    @patch('frontstage.controllers.case_controller.get_case_data')
    def test_access_survey_missing_collection_exercise_from_case_data(self, get_case_data):
        case_data = {
            "collection_instrument": collection_instrument_seft,
            "survey": survey,
            "business_party": business_party
        }
        get_case_data.return_value = case_data
        urls = ['access_survey', 'access-survey']
        for url in urls:
            with self.subTest(url=url):
                response = self.app.get(f'/surveys/{url}?case_id=8cdc01f9-656a-4715-a148-ffed0dbe1b04&business_party_id=0008279d-9425-4e28-897d-bfd876aa7f3f&'
                                        'survey_short_name=Bricks&ci_type=SEFT', headers=self.headers, follow_redirects=True)

                self.assertEqual(response.status_code, 500)
                self.assertTrue('An error has occurred'.encode() in response.data)

    @patch('frontstage.controllers.case_controller.get_case_data')
    def test_access_survey_missing_survey_from_case_data(self, get_case_data):
        case_data = {
            "collection_exercise": collection_exercise,
            "collection_instrument": collection_instrument_seft,
            "business_party": business_party
        }
        get_case_data.return_value = case_data

        response = self.app.get('/surveys/access-survey?case_id=8cdc01f9-656a-4715-a148-ffed0dbe1b04&business_party_id=0008279d-9425-4e28-897d-bfd876aa7f3f&'
                                'survey_short_name=Bricks&ci_type=SEFT', headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('An error has occurred'.encode() in response.data)

    @patch('frontstage.controllers.case_controller.get_case_data')
    def test_access_survey_missing_business_party_from_case_data(self, get_case_data):
        case_data = {
            "collection_exercise": collection_exercise,
            "collection_instrument": collection_instrument_seft,
            "survey": survey,
        }
        get_case_data.return_value = case_data

        response = self.app.get('/surveys/access-survey?case_id=8cdc01f9-656a-4715-a148-ffed0dbe1b04&business_party_id=0008279d-9425-4e28-897d-bfd876aa7f3f&'
                                'survey_short_name=Bricks&ci_type=SEFT', headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('An error has occurred'.encode() in response.data)

    def test_access_survey_without_request_arg_case_id(self):
        response = self.app.get('/surveys/access-survey?business_party_id=0008279d-9425-4e28-897d-bfd876aa7f3f&'
                                'survey_short_name=Bricks&ci_type=SEFT', headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 400)
        self.assertTrue('An error has occurred'.encode() in response.data)

    def test_access_survey_missing_request_arg_business_party_id(self):
        response = self.app.get('/surveys/access-survey?case_id=8cdc01f9-656a-4715-a148-ffed0dbe1b04&'
                                'survey_short_name=Bricks&ci_type=SEFT', headers=self.headers)

        self.assertEqual(response.status_code, 400)
        self.assertTrue('An error has occurred'.encode() in response.data)

    def test_access_survey_missing_request_arg_survey_short_name(self):
        response = self.app.get('/surveys/access-survey?case_id=8cdc01f9-656a-4715-a148-ffed0dbe1b04&business_party_id=0008279d-9425-4e28-897d-bfd876aa7f3f&'
                                'ci_type=SEFT', headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 400)
        self.assertTrue('An error has occurred'.encode() in response.data)

    def test_access_survey_missing_request_arg_ci_type(self):
        response = self.app.get('/surveys/access-survey?case_id=8cdc01f9-656a-4715-a148-ffed0dbe1b04&business_party_id=0008279d-9425-4e28-897d-bfd876aa7f3f&'
                                'survey_short_name=Bricks', headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 400)
        self.assertTrue('An error has occurred'.encode() in response.data)
