import json

import unittest
import requests_mock

from frontstage import app
from frontstage.exceptions.exceptions import ExternalServiceError
from frontstage.views.secure_messaging import get_collection_case


with open('tests/test_data/cases.json') as json_data:
    cases_data = json.load(json_data)

with open('tests/test_data/draft_message.json') as json_data:
    draft_message_data = json.load(json_data)

with open('tests/test_data/messages_get.json') as json_data:
    messages_get_data = json.load(json_data)

url_case_get_by_party = app.config['RM_CASE_GET_BY_PARTY'].format(app.config['RM_CASE_SERVICE'],
                                                                  "db036fd7-ce17-40c2-a8fc-932e7c228397")
url_sm_create_message = 'http://localhost:5050/message/send'
url_sm_save_draft = 'http://localhost:5050/draft/save'
url_sm_modify_draft = 'http://localhost:5050/draft/7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb/modify'
url_sm_get_draft = 'http://localhost:5050/draft/7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb'
url_sm_get_messages = 'http://localhost:5050/messages?limit=1000'
url_sm_get_single_draft = 'http://localhost:5050/draft/7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb'

encoded_jwt_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZWZyZXNoX3Rva2VuIjoiNmY5NjM0ZGEtYTI3ZS00ZDk3LWJhZjktNjN" \
                    "jOGRjY2IyN2M2IiwiYWNjZXNzX3Rva2VuIjoiMjUwMDM4YzUtM2QxOS00OGVkLThlZWMtODFmNTQyMDRjNDE1Iiwic2NvcGU" \
                    "iOlsiIl0sImV4cGlyZXNfYXQiOjE4OTM0NTk2NjEuMCwidXNlcm5hbWUiOiJ0ZXN0dXNlckBlbWFpbC5jb20iLCJyb2xlIjo" \
                    "icmVzcG9uZGVudCIsInBhcnR5X2lkIjoiZGIwMzZmZDctY2UxNy00MGMyLWE4ZmMtOTMyZTdjMjI4Mzk3In0.hh9sFpiPA-O" \
                    "8kugpDi3_GSDnxWh5rz2e5GQuBx7kmLM"


class TestSecureMessage(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.message_form = {
                              "secure-message-subject": "subject",
                              "secure-message-body": "body",
                              "submit": "Send"
                            }
        self.send_response = {
                              "msg_id": "7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb"
                            }
        self.send_error_response = {
                                     'subject': ['Subject field length must not be greater than 100.']
                                   }

    @requests_mock.mock()
    def test_get_collection_case_success(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=cases_data)

        collection_case_id = get_collection_case("db036fd7-ce17-40c2-a8fc-932e7c228397")

        self.assertEqual(collection_case_id, "7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb")

    # @requests_mock.mock()
    # def test_get_collection_case_not_found(self, mock_object):
    #     mock_object.get(url_case_get_by_party, status_code=204)
    #
    #     with app.app_context() as c:
    #         collection_case_response = get_collection_case("db036fd7-ce17-40c2-a8fc-932e7c228397")
    #
    #     self.assertEqual(collection_case_response.status_code, 302)

    @requests_mock.mock()
    def test_get_collection_case_failed(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=500)

        with app.app_context():
            self.assertRaises(ExternalServiceError, lambda: get_collection_case("db036fd7-ce17-40c2-a8fc-932e7c228397"))

    @requests_mock.mock()
    def test_create_message_get(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=cases_data)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.get("secure-message/create-message")

        self.assertEqual(response.status_code, 200)

    def test_create_message_get_not_logged_in(self):
        response = self.app.get("secure-message/create-message", follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("not logged in", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_create_message_post_success(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=cases_data)
        mock_object.post(url_sm_create_message, status_code=201, json=self.send_response)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.post("secure-message/create-message", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("Message sent", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_create_message_post_400(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=cases_data)
        mock_object.post(url_sm_create_message, status_code=400, json=self.send_error_response)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.post("secure-message/create-message", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("must be corrected", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_create_message_post_500(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=cases_data)
        mock_object.post(url_sm_create_message, status_code=500)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.post("secure-message/create-message", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("500", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_create_message_post_draft_new_success(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=cases_data)
        mock_object.post(url_sm_save_draft, status_code=201, json=self.send_response)
        mock_object.get(url_sm_get_draft, status_code=200, json=draft_message_data)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)
        self.message_form['submit'] = 'Save draft'

        response = self.app.post("secure-message/create-message", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("Draft saved", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_create_message_post_draft_new_400(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=cases_data)
        mock_object.post(url_sm_save_draft, status_code=400, json=self.send_error_response)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)
        self.message_form['submit'] = 'Save draft'

        response = self.app.post("secure-message/create-message", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("must be correct", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_create_message_post_draft_new_500(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=cases_data)
        mock_object.post(url_sm_save_draft, status_code=500)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)
        self.message_form['submit'] = 'Save draft'

        response = self.app.post("secure-message/create-message", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("errors", encoding='UTF-8'))

    @requests_mock.mock()
    def test_create_message_post_draft_old_success(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=cases_data)
        mock_object.put(url_sm_modify_draft, status_code=200, json=self.send_response)
        mock_object.get(url_sm_get_draft, status_code=200, json=draft_message_data)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)
        self.message_form['submit'] = 'Save draft'
        self.message_form['msg_id'] = '7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb'

        response = self.app.post("secure-message/create-message", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("Draft saved", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_create_message_post_draft_old_400(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=cases_data)
        mock_object.put(url_sm_modify_draft, status_code=400, json=self.send_error_response)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)
        self.message_form['submit'] = 'Save draft'
        self.message_form['msg_id'] = '7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb'

        response = self.app.post("secure-message/create-message", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("must be correct", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_create_message_post_draft_new_500(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=cases_data)
        mock_object.put(url_sm_modify_draft, status_code=500)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)
        self.message_form['submit'] = 'Save draft'
        self.message_form['msg_id'] = '7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb'

        response = self.app.post("secure-message/create-message", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("500", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_get_messages_success(self, mock_object):
        mock_object.get(url_sm_get_messages, status_code=200, json=messages_get_data)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.get("secure-message/messages/", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("aaaabbbbaaaa", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_get_messages_fail(self, mock_object):
        mock_object.get(url_sm_get_messages, status_code=500)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.get("secure-message/messages/", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("500", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_get_single_draft_success(self, mock_object):
        mock_object.get(url_sm_get_single_draft, status_code=200, json=draft_message_data)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.get("secure-message/draft/7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("Edit a draft message", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_get_single_draft_failure(self, mock_object):
        mock_object.get(url_sm_get_single_draft, status_code=500)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.get("secure-message/draft/7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("500", encoding='UTF-8') in response.data)
