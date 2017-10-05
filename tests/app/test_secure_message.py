import json

import unittest
import requests_mock

from frontstage import app
from frontstage.exceptions.exceptions import ExternalServiceError
from frontstage.views.secure_messaging import get_collection_case, get_party_ru_id, get_survey_id


with open('tests/test_data/cases.json') as json_data:
    cases_data = json.load(json_data)

with open("tests/test_data/cases_todo.json") as json_data:
    case_todo_data = json.load(json_data)

with open('tests/test_data/my_party.json') as json_data:
    party_data = json.load(json_data)

with open('tests/test_data/example_message.json') as json_data:
    example_message_data = json.load(json_data)

with open('tests/test_data/example_message_diff.json') as json_data:
    example_message_data_diff = json.load(json_data)

with open('tests/test_data/messages_get.json') as json_data:
    messages_get_data = json.load(json_data)

with open('tests/test_data/thread.json') as json_data:
    thread_data = json.load(json_data)

url_case_get_by_party = app.config['RM_CASE_GET_BY_PARTY'].format(app.config['RM_CASE_SERVICE'],
                                                                  "db036fd7-ce17-40c2-a8fc-932e7c228397", "")
url_ru_id_get_by_party = app.config['RAS_PARTY_GET_BY_RESPONDENT'].format(app.config['RAS_PARTY_SERVICE'],
                                                                          "db036fd7-ce17-40c2-a8fc-932e7c228397")

url_sm_create_message = app.config['CREATE_MESSAGE_API_URL']
url_sm_save_draft = app.config['DRAFT_SAVE_API_URL']
url_sm_modify_draft = app.config['DRAFT_PUT_API_URL'].format('7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb')
url_sm_modify_message = app.config['MESSAGE_MODIFY_URL'].format('7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb')
url_sm_get_single_draft = app.config['DRAFT_GET_API_URL'].format('7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb')
url_sm_get_messages = app.config['MESSAGES_API_URL']
url_api_get_messages = app.config['RAS_FRONTSTAGE_API_SERVICE'] + app.config['GET_MESSAGES_URL']
url_sm_get_single_message = app.config['MESSAGE_GET_URL'].format('7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb')
url_sm_get_labels = app.config['LABELS_GET_API_URL']
url_sm_get_thread = app.config['THREAD_GET_API_URL'].format('7bc5d41b-0549-40b3-ba76-42f6d4cf3fde')

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
                              "submit": "Send",
                              "secure-message-thread-id": "7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb"
                            }
        self.send_response = {
                              "msg_id": "7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb"
                            }
        self.send_error_response = {
                                     'subject': ['Subject field length must not be greater than 100.']
                                   }

    @requests_mock.mock()
    def test_get_collection_case_success(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=case_todo_data)

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

    # @requests_mock.mock()
    # def test_get_ru_id_not_found(self, mock_object):
    #     mock_object.get(url_ru_id_get_by_party, status_code=404)
    #
    #     with app.app_context():
    #         self.assertRaises(ExternalServiceError, lambda: get_party_ru_id("db036fd7-ce17-40c2-a8fc-932e7c228397"))

    @requests_mock.mock()
    def test_get_ru_id_failure(self, mock_object):
        mock_object.get(url_ru_id_get_by_party, status_code=500)

        with app.app_context():
            self.assertRaises(ExternalServiceError, lambda: get_party_ru_id("db036fd7-ce17-40c2-a8fc-932e7c228397"))

    @requests_mock.mock()
    def test_get_survey_id_failure(self, mock_object):
        mock_object.get(url_ru_id_get_by_party, status_code=500)

        with app.app_context():
            self.assertRaises(ExternalServiceError, lambda: get_survey_id("db036fd7-ce17-40c2-a8fc-932e7c228397"))

    @requests_mock.mock()
    def test_create_message_get(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=case_todo_data)
        mock_object.get(url_ru_id_get_by_party, status_code=200, json=party_data)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.get("secure-message/create-message")

        self.assertEqual(response.status_code, 200)

    def test_create_message_get_not_logged_in(self):
        response = self.app.get("secure-message/create-message", follow_redirects=True)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(bytes("Error - not signed in", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_create_message_post_success(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=case_todo_data)
        mock_object.get(url_ru_id_get_by_party, status_code=200, json=party_data)
        mock_object.post(url_sm_create_message, status_code=201, json=self.send_response)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.post("secure-message/create-message", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("Message sent", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_create_message_post_400(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=case_todo_data)
        mock_object.get(url_ru_id_get_by_party, status_code=200, json=party_data)
        mock_object.post(url_sm_create_message, status_code=400, json=self.send_error_response)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)
        message_form = self.message_form
        message_form['secure-message-thread-id'] = ''

        response = self.app.post("secure-message/create-message", data=message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("must be corrected", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_create_message_post_500(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=case_todo_data)
        mock_object.get(url_ru_id_get_by_party, status_code=200, json=party_data)
        mock_object.post(url_sm_create_message, status_code=500)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.post("secure-message/create-message", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue(bytes("500", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_create_message_post_draft_new_success(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=case_todo_data)
        mock_object.get(url_ru_id_get_by_party, status_code=200, json=party_data)
        mock_object.post(url_sm_save_draft, status_code=201, json=self.send_response)
        mock_object.get(url_sm_get_single_draft, status_code=200, json=example_message_data)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)
        self.message_form['submit'] = 'Save draft'

        response = self.app.post("secure-message/create-message", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("Draft saved", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_create_message_post_draft_new_400(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=case_todo_data)
        mock_object.get(url_ru_id_get_by_party, status_code=200, json=party_data)
        mock_object.post(url_sm_save_draft, status_code=400, json=self.send_error_response)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)
        self.message_form['submit'] = 'Save draft'
        self.message_form['secure-message-thread-id'] = ''

        response = self.app.post("secure-message/create-message", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("must be correct", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_create_message_post_draft_new_500(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=case_todo_data)
        mock_object.get(url_ru_id_get_by_party, status_code=200, json=party_data)
        mock_object.post(url_sm_save_draft, status_code=500)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)
        self.message_form['submit'] = 'Save draft'

        response = self.app.post("secure-message/create-message", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue(bytes("errors", encoding='UTF-8'))

    @requests_mock.mock()
    def test_create_message_post_draft_old_success(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=case_todo_data)
        mock_object.get(url_ru_id_get_by_party, status_code=200, json=party_data)
        mock_object.put(url_sm_modify_draft, status_code=200, json=self.send_response)
        mock_object.get(url_sm_get_single_draft, status_code=200, json=example_message_data)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)
        self.message_form['submit'] = 'Save draft'
        self.message_form['msg_id'] = '7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb'

        response = self.app.post("secure-message/create-message", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("Draft saved", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_create_message_post_draft_old_400(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=case_todo_data)
        mock_object.get(url_ru_id_get_by_party, status_code=200, json=party_data)
        mock_object.put(url_sm_modify_draft, status_code=400, json=self.send_error_response)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)
        self.message_form['submit'] = 'Save draft'
        self.message_form['msg_id'] = '7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb'
        self.message_form['secure-message-thread-id'] = ''

        response = self.app.post("secure-message/create-message", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("must be correct", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_create_message_post_draft_new_500_with_msg_id(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=case_todo_data)
        mock_object.get(url_ru_id_get_by_party, status_code=200, json=party_data)
        mock_object.put(url_sm_modify_draft, status_code=500)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)
        self.message_form['submit'] = 'Save draft'
        self.message_form['msg_id'] = '7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb'

        response = self.app.post("secure-message/create-message", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue(bytes("500", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_get_messages_success(self, mock_object):
        mock_object.get(url_api_get_messages, status_code=200, json=messages_get_data)
        mock_object.get(url_sm_get_labels, status_code=200, json={'name': '', 'total': ''})
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.get("secure-message/messages/", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("aaaabbbbaaaa", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_get_messages_fail(self, mock_object):
        mock_object.get(url_api_get_messages, status_code=500)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.get("secure-message/messages/", data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue(bytes("500", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_get_single_draft_success(self, mock_object):
        mock_object.get(url_sm_get_single_draft, status_code=200, json=example_message_data)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.get("secure-message/DRAFT/7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb",
                                data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("Edit draft message", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_get_single_thread_draft_success(self, mock_object):
        mock_object.get(url_sm_get_single_draft, status_code=200, json=example_message_data_diff)
        mock_object.get(url_sm_get_thread, status_code=200, json=thread_data)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.get("secure-message/DRAFT/7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb",
                                data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("asdasd", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_get_single_draft_thread_failure(self, mock_object):
        mock_object.get(url_sm_get_single_draft, status_code=200, json=example_message_data_diff)
        mock_object.get(url_sm_get_thread, status_code=500)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.get("secure-message/DRAFT/7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb",
                                data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 500)
        self.assertTrue(bytes("Server error", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_get_single_message_success(self, mock_object):
        mock_object.put(url_sm_modify_message, status_code=200, json=example_message_data)
        mock_object.get(url_sm_get_single_message, status_code=200, json=example_message_data)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.get("secure-message/INBOX/7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb", data=self.message_form)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("Reply", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_get_single_message_get_failure(self, mock_object):
        mock_object.put(url_sm_modify_message, status_code=200, json=example_message_data)
        mock_object.get(url_sm_get_single_message, status_code=500)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.get("secure-message/INBOX/7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb", data=self.message_form)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(bytes("errors", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_get_single_message_modify_failure(self, mock_object):
        mock_object.get(url_sm_get_single_message, status_code=200, json=example_message_data)
        mock_object.put(url_sm_modify_message, status_code=500)
        self.app.set_cookie('localhost', 'authorization', encoded_jwt_token)

        response = self.app.get("secure-message/INBOX/7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb",
                                data=self.message_form, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("Reply", encoding='UTF-8') in response.data)
