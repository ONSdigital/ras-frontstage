import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from frontstage.exceptions.exceptions import IncorrectAccountAccessError
from tests.integration.mocked_services import (conversation_json, conversation_list_json,
                                               encoded_jwt_token, url_get_thread, url_get_threads,
                                               url_send_message, url_get_conversation_count, url_banner_api)


def create_api_error(status_code, data=None):
    error_json = {
        "error": {
            "status_code": status_code,
            "data": data
        }
    }
    return error_json


class TestSecureMessage(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.app.set_cookie('localhost', 'authorization', 'session_key')
        self.patcher = patch('redis.StrictRedis.get', return_value=encoded_jwt_token)
        self.patcher.start()
        self.message_form = {
            "subject": "subject",
            "body": "body",
            "send": "Send",
            "thread_id": "7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb",
        }
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54" # NOQA
        }

    def tearDown(self):
        self.patcher.stop()

    @requests_mock.mock()
    def test_get_thread_success(self, mock_request):
        mock_request.get(url_banner_api, status_code=204)
        mock_request.get(url_get_thread, json={'messages': [conversation_json], 'is_closed': False})
        mock_request.get(url_get_conversation_count, json={'total': 0})

        response = self.app.get("secure-message/threads/9e3465c0-9172-4974-a7d1-3a01592d1594",
                                headers=self.headers, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Peter Griffin'.encode() in response.data)
        self.assertTrue('testy2'.encode() in response.data)
        self.assertTrue('something else'.encode() in response.data)
        self.assertIn("Please note, this system should not be used to inform us of changes to".encode(), response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.conversation_controller.try_message_count_from_session")
    def test_get_thread_failure(self, mock_request, message_count):
        mock_request.get(url_banner_api, status_code=204)
        message_count.return_value = 0
        conversation_json_copy = conversation_json.copy()
        del conversation_json_copy['@business_details']
        mock_request.get(url_get_thread, json={'messages': [conversation_json_copy]})

        response = self.app.get("secure-message/threads/9e3465c0-9172-4974-a7d1-3a01592d1594", headers=self.headers,
                                follow_redirects=True)
        self.assertEqual(response.status_code, 500)

    @requests_mock.mock()
    @patch("frontstage.controllers.conversation_controller.try_message_count_from_session")
    def test_create_message_get(self, mock_request, message_count):
        mock_request.get(url_banner_api, status_code=204)
        message_count.return_value = 0
        response = self.app.get("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Create message'.encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.conversation_controller.try_message_count_from_session")
    def test_create_message_post_success(self, mock_request, message_count):
        mock_request.get(url_banner_api, status_code=204)
        message_count.return_value = 0
        sent_message_response = {'msg_id': 'd43b6609-0875-4ef8-a34e-f7df1bcc8029', 'status': '201',
                                 'thread_id': '8caeff79-6067-4f2a-96e0-08617fdeb496'}
        mock_request.post(url_send_message, json=sent_message_response)
        mock_request.get(url_get_threads, json=conversation_list_json)

        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('ONS Business Surveys Team'.encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.conversation_controller.try_message_count_from_session")
    def test_create_message_post_success_api_failure(self, mock_request, message_count):
        mock_request.get(url_banner_api, status_code=204)
        message_count.return_value = 0
        mock_request.post(url_send_message, status_code=500)

        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('An error has occurred'.encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.conversation_controller.try_message_count_from_session")
    def test_create_message_post_bad_gateway(self, mock_request, message_count):
        mock_request.get(url_banner_api, status_code=204)
        message_count.return_value = 0
        mock_request.post(url_send_message, status_code=502)

        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('An error has occurred'.encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.conversation_controller.try_message_count_from_session")
    def test_create_message_post_no_body(self, mock_request, message_count):
        mock_request.get(url_banner_api, status_code=204)
        message_count.return_value = 0
        del self.message_form['body']

        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please enter a message'.encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.conversation_controller.try_message_count_from_session")
    def test_create_message_post_no_subject(self, mock_request, message_count):
        mock_request.get(url_banner_api, status_code=204)
        message_count.return_value = 0
        del self.message_form['subject']

        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please enter a subject'.encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.conversation_controller.try_message_count_from_session")
    def test_create_message_post_whitespace_subject(self, mock_request, message_count):
        mock_request.get(url_banner_api, status_code=204)
        message_count.return_value = 0
        self.message_form['subject'] = ' '

        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please enter a subject'.encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.conversation_controller.try_message_count_from_session")
    def test_create_message_post_body_too_long(self, mock_request, message_count):
        mock_request.get(url_banner_api, status_code=204)
        message_count.return_value = 0
        self.message_form['body'] = 'a' * 50100

        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Body field length must not be greater than 50000'.encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.conversation_controller.try_message_count_from_session")
    def test_create_message_post_subject_too_long(self, mock_request, message_count):
        mock_request.get(url_banner_api, status_code=204)
        message_count.return_value = 0
        self.message_form['subject'] = 'a' * 110

        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Subject field length must not be greater than 100'.encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.conversation_controller.try_message_count_from_session")
    def test_create_message_post_no_case_id(self, mock_request, message_count):
        mock_request.get(url_banner_api, status_code=204)
        message_count.return_value = 0
        sent_message_response = {'msg_id': 'd43b6609-0875-4ef8-a34e-f7df1bcc8029', 'status': '201',
                                 'thread_id': '8caeff79-6067-4f2a-96e0-08617fdeb496'}
        mock_request.post(url_send_message, json=sent_message_response)
        mock_request.get(url_get_threads, json=conversation_list_json)

        response = self.app.post("/secure-message/create-message/?ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)
        # case id is optional
        self.assertEqual(response.status_code, 200)
        self.assertTrue('ONS Business Surveys Team'.encode() in response.data)

    @requests_mock.mock()
    @patch("frontstage.controllers.conversation_controller.try_message_count_from_session")
    def test_create_message_post_no_survey_id(self, mock_request, message_count):
        mock_request.get(url_banner_api, status_code=204)
        message_count.return_value = 0
        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 400)

    @requests_mock.mock()
    @patch("frontstage.controllers.conversation_controller.try_message_count_from_session")
    def test_create_message_post_no_ru_ref(self, mock_request, message_count):
        mock_request.get(url_banner_api, status_code=204)
        message_count.return_value = 0
        response = self.app.post("/secure-message/create-message/?case_id=123&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 400)

    @requests_mock.mock()
    @patch("frontstage.controllers.conversation_controller.try_message_count_from_session")
    def test_get_thread_wrong_account(self, mock_request, message_count):
        mock_request.get(url_banner_api, status_code=204)
        message_count.return_value = 0
        mock_request.get(url_get_thread, status_code=404, json={'messages': [conversation_json], 'is_closed': False})

        self.assertRaises(IncorrectAccountAccessError)

    @requests_mock.mock()
    @patch('frontstage.controllers.conversation_controller._create_get_conversation_headers')
    @patch("frontstage.controllers.conversation_controller.try_message_count_from_session")
    def test_secure_message_unauthorized_return(self, mock_request, authorization, message_count):
        mock_request.get(url_banner_api, status_code=204)
        message_count.return_value = 0
        authorization.return_value = {"Authorization": "wrong authorization"}

        mock_request.get(url_get_thread, status_code=403)

        response = self.app.get("secure-message/threads/9e3465c0-9172-4974-a7d1-3a01592d1594", headers=self.headers,
                                follow_redirects=True)
        self.assertTrue('The page you are trying to view is not for this account.'.encode() in response.data)
