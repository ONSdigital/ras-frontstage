import json
import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app


url_get_messages = app.config['RAS_FRONTSTAGE_API_SERVICE'] + app.config['GET_MESSAGES_URL']
with open('tests/test_data/secure_messaging/messages_get.json') as json_data:
    messages_get = json.load(json_data)
url_get_message = app.config['RAS_FRONTSTAGE_API_SERVICE'] + app.config['GET_MESSAGE_URL']
with open('tests/test_data/secure_messaging/message.json') as json_data:
    message = json.load(json_data)
url_send_message = app.config['RAS_FRONTSTAGE_API_SERVICE'] + app.config['SEND_MESSAGE_URL']


encoded_jwt = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZWZyZXNoX3Rva2VuIjoiNmY5NjM0ZGEtYTI3ZS00ZDk3LWJhZjktNjN" \
                    "jOGRjY2IyN2M2IiwiYWNjZXNzX3Rva2VuIjoiMjUwMDM4YzUtM2QxOS00OGVkLThlZWMtODFmNTQyMDRjNDE1Iiwic2NvcGU" \
                    "iOlsiIl0sImV4cGlyZXNfYXQiOjE4OTM0NTk2NjEuMCwidXNlcm5hbWUiOiJ0ZXN0dXNlckBlbWFpbC5jb20iLCJyb2xlIjo" \
                    "icmVzcG9uZGVudCIsInBhcnR5X2lkIjoiZGIwMzZmZDctY2UxNy00MGMyLWE4ZmMtOTMyZTdjMjI4Mzk3In0.hh9sFpiPA-O" \
                    "8kugpDi3_GSDnxWh5rz2e5GQuBx7kmLM"


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
        self.app.set_cookie('localhost', 'authorization', encoded_jwt)
        self.patcher = patch('redis.StrictRedis.get', return_value=encoded_jwt)
        self.patcher.start()
        self.message_form = {
                              "secure-message-subject": "subject",
                              "secure-message-body": "body",
                              "submit": "Send",
                              "secure-message-thread-id": "7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb",
                            }
        self.headers = {'jwt': encoded_jwt}

    def tearDown(self):
        self.patcher.stop()

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
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_get_messages_api_error_FA002(self, mock_request):
        unread_total_fail_json = {**messages_get, **create_api_error(500)}
        del unread_total_fail_json['unread_messages_total']
        mock_request.get(url_get_messages, json=unread_total_fail_json)

        response = self.app.get("/secure-message/messages", headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('The European languages are members of the same family'.encode() in response.data)

    @requests_mock.mock()
    def test_get_message_success(self, mock_request):
        mock_request.get(url_get_message, json=message)

        response = self.app.get("/secure-message/INBOX/29000d7b-dfd8-47fa-8e15-5650a985243b", headers=self.headers, follow_redirects=True)

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
        response = self.app.get("/secure-message/create-message", headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Create message'.encode() in response.data)

    @requests_mock.mock()
    def test_create_message_post_success(self, mock_request):
        sent_message_response = {'msg_id': 'd43b6609-0875-4ef8-a34e-f7df1bcc8029', 'status': '201', 'thread_id': '8caeff79-6067-4f2a-96e0-08617fdeb496'}
        mock_request.post(url_send_message, json=sent_message_response)

        response = self.app.post("/secure-message/create-message", data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Message sent'.encode() in response.data)

    @requests_mock.mock()
    def test_create_message_draft_success(self, mock_request):
        sent_message_response = {'msg_id': 'd43b6609-0875-4ef8-a34e-f7df1bcc8029', 'status': '201', 'thread_id': '8caeff79-6067-4f2a-96e0-08617fdeb496'}
        mock_request.post(url_send_message, json=sent_message_response)
        mock_request.get(url_get_message, json=message)
        self.message_form['msg_id'] = 'test_msg_id'
        self.message_form['submit'] = 'Save draft'

        response = self.app.post("/secure-message/create-message", data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Draft saved'.encode() in response.data)

    @requests_mock.mock()
    def test_create_message_post_success_api_failure(self, mock_request):
        mock_request.post(url_send_message, status_code=500)

        response = self.app.post("/secure-message/create-message", data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_create_message_post_success_api_failure(self, mock_request):
        mock_request.post(url_send_message, status_code=500)

        response = self.app.post("/secure-message/create-message", data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    @requests_mock.mock()
    def test_create_message_post_bad_gateway(self, mock_request):
        mock_request.post(url_send_message, status_code=502)

        response = self.app.post("/secure-message/create-message", data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error'.encode() in response.data)

    # This error is for a bad request (form errors)
    @requests_mock.mock()
    def test_create_message_post_success_api_error(self, mock_request):
        form_errors = {'form_errors': {'subject': ['Please enter a subject']}}
        mock_request.post(url_send_message, status_code=400, json=create_api_error(400, form_errors))

        response = self.app.post("/secure-message/create-message", data=self.message_form, headers=self.headers, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue('Please enter a subject'.encode() in response.data)
