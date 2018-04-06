import json
import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app

url_get_thread = app.config['RAS_SECURE_MESSAGING_SERVICE'] + "v2/threads/9e3465c0-9172-4974-a7d1-3a01592d1594"
url_get_threads = app.config['RAS_SECURE_MESSAGING_SERVICE'] + "threads"
with open('tests/test_data/conversation.json') as json_data:
    conversation_json = json.load(json_data)
with open('tests/test_data/conversation_list.json') as json_data:
    conversation_list_json = json.load(json_data)

url_get_messages = app.config['RAS_FRONTSTAGE_API_SERVICE'] + app.config['GET_MESSAGES_URL']
with open('tests/test_data/secure_messaging/messages_get.json') as json_data:
    messages_get = json.load(json_data)
url_get_message = app.config['RAS_FRONTSTAGE_API_SERVICE'] + app.config['GET_MESSAGE_URL']
with open('tests/test_data/secure_messaging/message.json') as json_data:
    message = json.load(json_data)
url_send_message = app.config['RAS_FRONTSTAGE_API_SERVICE'] + app.config['SEND_MESSAGE_URL']


encoded_jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoicmVzcG9uZGVudCIsImFjY2Vzc190b2tlbiI6ImI5OWIyMjA0LWYxM" \
              "DAtNDcxZS1iOTQ1LTIyN2EyNmVhNjljZCIsInJlZnJlc2hfdG9rZW4iOiIxZTQyY2E2MS02ZDBkLTQxYjMtODU2Yy02YjhhMDhlYmI" \
              "yZTMiLCJleHBpcmVzX2F0IjoxNzM4MTU4MzI4LjAsInBhcnR5X2lkIjoiZjk1NmU4YWUtNmUwZi00NDE0LWIwY2YtYTA3YzFhYTNlM" \
              "zdiIn0.7W9yikGtX2gbKLclxv-dajcJ2NL0Nb_HDVqHrCrYvQE"


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
        self.patcher = patch('redis.StrictRedis.get', return_value=encoded_jwt)
        self.patcher.start()
        self.message_form = {
                              "subject": "subject",
                              "body": "body",
                              "send": "Send",
                              "thread_id": "7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb",
                            }
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
            }

    def tearDown(self):
        self.patcher.stop()

    @requests_mock.mock()
    def test_get_thread_success(self, mock_request):
        mock_request.get(url_get_thread, json={'messages': [conversation_json]})

        response = self.app.get("secure-message/thread/9e3465c0-9172-4974-a7d1-3a01592d1594", headers=self.headers, follow_redirects=True)
        self.assertTrue(response.status_code, 200)
        self.assertTrue('Peter Griffin'.encode() in response.data)
        self.assertTrue('testy2'.encode() in response.data)
        self.assertTrue('something else'.encode() in response.data)

    @requests_mock.mock()
    def test_get_thread_failure(self, mock_request):
        conversation_json_copy = conversation_json.copy()
        del conversation_json_copy['@ru_id']
        mock_request.get(url_get_thread, json={'messages': [conversation_json_copy]})

        response = self.app.get("secure-message/thread/9e3465c0-9172-4974-a7d1-3a01592d1594", headers=self.headers, follow_redirects=True)
        self.assertTrue(response.status_code, 500)
        self.assertTrue('Something has gone wrong with the website.'.encode() in response.data)

    @requests_mock.mock()
    def test_get_messages_success(self, mock_request):
        mock_request.get(url_get_messages, json=messages_get)

        response = self.app.get("/secure-message/messages", headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('The European languages are members of the same family'.encode() in response.data)

    @requests_mock.mock()
    def test_get_messages_api_failure(self, mock_request):
        mock_request.get(url_get_messages, status_code=500)

        response = self.app.get("/secure-message/messages", headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_get_messages_api_error_bad_gateway(self, mock_request):
        mock_request.get(url_get_messages, status_code=502)

        response = self.app.get("/secure-message/messages", headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        print(response.data)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_get_messages_api_error_FA002(self, mock_request):
        unread_total_fail_json = {**messages_get, **create_api_error(500)}
        del unread_total_fail_json['unread_messages_total']
        mock_request.get(url_get_messages, json=unread_total_fail_json)

        response = self.app.get("/secure-message/messages", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('The European languages are members of the same family'.encode() in response.data)

    @requests_mock.mock()
    def test_get_message_success(self, mock_request):
        mock_request.get(url_get_message, json=message)

        response = self.app.get("/secure-message/INBOX/29000d7b-dfd8-47fa-8e15-5650a985243b", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('The European languages are members of the same family'.encode() in response.data)
        self.assertTrue('Test draft'.encode() in response.data)

    @requests_mock.mock()
    def test_get_message_api_failure(self, mock_request):
        mock_request.get(url_get_message, status_code=500)

        response = self.app.get("/secure-message/INBOX/29000d7b-dfd8-47fa-8e15-5650a985243b", headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_get_message_api_error_FA003(self, mock_request):
        mock_request.get(url_get_message, status_code=502)

        response = self.app.get("/secure-message/INBOX/29000d7b-dfd8-47fa-8e15-5650a985243b", headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    def test_create_message_get(self):
        response = self.app.get("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789", headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Create message'.encode() in response.data)

    @requests_mock.mock()
    def test_create_message_post_success(self, mock_request):
        sent_message_response = {'msg_id': 'd43b6609-0875-4ef8-a34e-f7df1bcc8029', 'status': '201',
                                 'thread_id': '8caeff79-6067-4f2a-96e0-08617fdeb496'}
        mock_request.post(url_send_message, json=sent_message_response)
        mock_request.get(url_get_messages, json=messages_get)
        mock_request.get(url_get_threads, json=conversation_list_json)

        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('ONS Business Surveys Team'.encode() in response.data)

    @requests_mock.mock()
    def test_create_message_draft_success(self, mock_request):
        sent_message_response = {'msg_id': 'd43b6609-0875-4ef8-a34e-f7df1bcc8029', 'status': '201', 'thread_id': '8caeff79-6067-4f2a-96e0-08617fdeb496'}
        mock_request.post(url_send_message, json=sent_message_response)
        mock_request.get(url_get_message, json=message)
        self.message_form['msg_id'] = 'test_msg_id'
        del self.message_form['send']
        self.message_form['save_draft'] = 'Save Draft'

        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Draft saved'.encode() in response.data)

    @requests_mock.mock()
    def test_create_message_post_success_api_failure(self, mock_request):
        mock_request.post(url_send_message, status_code=500)

        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_create_message_post_bad_gateway(self, mock_request):
        mock_request.post(url_send_message, status_code=502)

        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    def test_create_message_post_no_body(self):
        del self.message_form['body']

        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please enter a message'.encode() in response.data)

    def test_create_message_post_no_subject(self):
        del self.message_form['subject']

        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please enter a subject'.encode() in response.data)

    def test_create_message_post_whitespace_subject(self):
        self.message_form['subject'] = ' '

        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please enter a subject'.encode() in response.data)

    @requests_mock.mock()
    def test_create_message_draft_no_body_or_subject(self, mock_request):
        sent_message_response = {'msg_id': 'd43b6609-0875-4ef8-a34e-f7df1bcc8029', 'status': '201', 'thread_id': '8caeff79-6067-4f2a-96e0-08617fdeb496'}
        mock_request.post(url_send_message, json=sent_message_response)
        mock_request.get(url_get_message, json=message)
        self.message_form['msg_id'] = 'test_msg_id'
        del self.message_form['send']
        self.message_form['save_draft'] = 'Save Draft'
        del self.message_form['body']
        del self.message_form['subject']

        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Draft saved'.encode() in response.data)

    def test_create_message_post_body_too_long(self):
        self.message_form['body'] = 'a' * 10100

        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Body field length must not be greater than 10000'.encode() in response.data)

    def test_create_message_post_subject_too_long(self):
        self.message_form['subject'] = 'a' * 110

        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Subject field length must not be greater than 100'.encode() in response.data)

    @requests_mock.mock()
    def test_create_message_post_no_case_id(self, mock_request):
        sent_message_response = {'msg_id': 'd43b6609-0875-4ef8-a34e-f7df1bcc8029', 'status': '201',
                                 'thread_id': '8caeff79-6067-4f2a-96e0-08617fdeb496'}
        mock_request.post(url_send_message, json=sent_message_response)
        mock_request.get(url_get_messages, json=messages_get)
        mock_request.get(url_get_threads, json=conversation_list_json)

        response = self.app.post("/secure-message/create-message/?ru_ref=456&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)
        # case id is optional
        self.assertEqual(response.status_code, 200)
        self.assertTrue('ONS Business Surveys Team'.encode() in response.data)

    def test_create_message_post_no_survey_id(self):
        response = self.app.post("/secure-message/create-message/?case_id=123&ru_ref=456",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 400)

    def test_create_message_post_no_ru_ref(self):
        response = self.app.post("/secure-message/create-message/?case_id=123&survey=789",
                                 data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 400)
