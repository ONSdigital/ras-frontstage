import logging
import unittest
from unittest.mock import patch

from requests.models import Response
from structlog import wrap_logger

from frontstage import app
from frontstage.exceptions.exceptions import ApiError
from tests.integration.mocked_services import active_iac, encrypted_enrolment_code, enrolment_code, inactive_iac, \
    url_validate_enrolment


logger = wrap_logger(logging.getLogger(__name__))


class TestAddSurvey(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie('localhost', 'authorization', 'session_key')
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
        }

    def test_add_survey_get_form(self):
        response = self.app.get('/surveys/add-survey')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Add a survey'.encode() in response.data)

    @patch('frontstage.controllers.iac_controller.get_iac_from_enrolment')
    @patch('frontstage.common.cryptographer.Cryptographer.encrypt')
    def test_add_survey_post_success(self, encrypt_enrolment_code, get_iac_by_enrolment_code):
        encrypt_enrolment_code.return_value = encrypted_enrolment_code.encode()
        get_iac_by_enrolment_code.return_value = active_iac

        response = self.app.post('/surveys/add-survey', data={'enrolment_code': enrolment_code})

        self.assertEqual(response.status_code, 302)
        self.assertTrue('confirm-organisation-survey'.encode() in response.data, 'Did not redirect to expected confirm organisation and survey page')

    @patch('frontstage.controllers.iac_controller.get_iac_from_enrolment')
    def test_add_survey_post_no_iac_found_for_enrolment_code(self, get_iac_by_enrolment_code):
        get_iac_by_enrolment_code.return_value = None

        response = self.app.post('/surveys/add-survey', data={'enrolment_code': enrolment_code})

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Enter a valid enrolment code'.encode() in response.data)
        self.assertTrue('Please re-enter the code and try again'.encode() in response.data)

    @patch('frontstage.controllers.iac_controller.get_iac_from_enrolment')
    def test_add_survey_post_iac_not_active_for_enrolment_code(self, get_iac_by_enrolment_code):
        get_iac_by_enrolment_code.return_value = inactive_iac

        response = self.app.post('/surveys/add-survey', data={'enrolment_code': enrolment_code})

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Enter a valid enrolment code'.encode() in response.data)
        self.assertTrue('Please re-enter the code and try again'.encode() in response.data)

    @patch('frontstage.controllers.iac_controller.get_iac_from_enrolment')
    def test_add_survey_enrolment_code_already_used(self, get_iac_by_enrolment_code):
        error_response = Response()
        error_response.status_code = 400
        error_response.url = url_validate_enrolment
        error = ApiError(logger, error_response)
        error.status_code = 400

        get_iac_by_enrolment_code.side_effect = error

        response = self.app.post('/surveys/add-survey', data={'enrolment_code': enrolment_code})

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Enter a valid enrolment code'.encode() in response.data)
        self.assertTrue('Please re-enter the code and try again'.encode() in response.data)

    @patch('frontstage.controllers.iac_controller.get_iac_from_enrolment')
    def test_add_survey_post_fail(self, get_iac_by_enrolment_code):
        error_response = Response()
        error_response.status_code = 500
        error_response.url = url_validate_enrolment
        error = ApiError(logger, error_response)
        error.status_code = 500

        get_iac_by_enrolment_code.side_effect = error

        response = self.app.post('/surveys/add-survey', data={'enrolment_code': enrolment_code})

        self.assertEqual(response.status_code, 500)
        self.assertTrue('An error has occurred'.encode() in response.data)

    def test_add_survey_invalid_enrolment_code_length(self):

        response = self.app.post('/surveys/add-survey', data={'enrolment_code': '1234'})

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Enter a valid enrolment code'.encode() in response.data)
        self.assertTrue('Please re-enter the code and try again'.encode() in response.data)
