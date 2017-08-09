import json

import unittest
import requests_mock

from frontstage import app
from frontstage.exceptions.exceptions import ExternalServiceError
from frontstage.views.secure_messaging import get_collection_case


with open('tests/test_data/cases.json') as json_data:
    cases_data = json.load(json_data)

url_case_get_by_party = app.config['RM_CASE_GET_BY_PARTY'].format(app.config['RM_CASE_SERVICE'],
                                                                  "db036fd7-ce17-40c2-a8fc-932e7c228397")
encoded_jwt_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJyZWZyZXNoX3Rva2VuIjoiNDljZmI5YjYtMDM1Ny00OGFiLWE1ZTQtZDE" \
                    "0ZGFmOWRhODRiIiwiYWNjZXNzX3Rva2VuIjoiNDg4MTc0NmMtY2UwNS00MzY2LWJlYzgtNmJiMGFkNjAyMzI2Iiwic2NvcGU" \
                    "iOlsiIl0sImV4cGlyZXNfYXQiOjE1MDIyODc1NTEuNTM2NjU2OSwidXNlcm5hbWUiOiJ0ZXN0dXNlckBlbWFpbC5jb20iLCJ" \
                    "yb2xlIjoicmVzcG9uZGVudCIsInBhcnR5X2lkIjoiZGIwMzZmZDctY2UxNy00MGMyLWE4ZmMtOTMyZTdjMjI4Mzk3In0.YCI" \
                    "840GM7ihdSPKRtHI8ab33sQbZFkJfpD3mX82LFrg"


class TestSecureMessage(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.message_form = {
                              "secure-message-subject": "subject",
                              "secure-message-body" "body",
                              ""
        }

    @requests_mock.mock()
    def test_get_collection_case_success(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=200, json=cases_data)

        collection_case_id = get_collection_case("db036fd7-ce17-40c2-a8fc-932e7c228397")

        self.assertEqual(collection_case_id, "7bc5d41b-0549-40b3-ba76-42f6d4cf3fdb")

    @requests_mock.mock()
    def test_get_collection_case_not_found(self, mock_object):
        mock_object.get(url_case_get_by_party, status_code=204)

        with app.app_context():
            collection_case_response = get_collection_case("db036fd7-ce17-40c2-a8fc-932e7c228397")

        self.assertEqual(collection_case_response.status_code, 302)
        self.assertTrue(bytes("errors", encoding='UTF-8') in collection_case_response.data)

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
        self.assertTrue(bytes("Create message", encoding='UTF-8') in response.data)

    def test_create_message_get_not_logged_in(self):
        response = self.app.get("secure-message/create-message")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("not logged in", encoding='UTF-8') in response.data)

    @requests_mock.mock()
    def test_create_message_post_success(self, mock_object):
        response = self.app.post("secure-message/create-message")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(bytes("not logged in", encoding='UTF-8') in response.data)
