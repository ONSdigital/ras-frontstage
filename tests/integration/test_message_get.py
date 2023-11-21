import copy
import unittest
from unittest.mock import patch

import requests_mock

from frontstage import app
from frontstage.views.secure_messaging.message_get import get_msg_to
from tests.integration.mocked_services import (
    encoded_jwt_token,
    message_json,
    url_banner_api,
    url_get_conversation_count,
    url_get_survey_long_name,
    url_get_thread,
)


class TestMessageGet(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie("authorization", "session_key")
        self.patcher = patch("redis.StrictRedis.get", return_value=encoded_jwt_token)
        self.patcher.start()
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
        }

    def tearDown(self):
        self.patcher.stop()

    def test_get_msg_to_returns_group_if_no_internal_user(self):
        msg = {"something": "somethings"}
        conversation = [msg, copy.deepcopy(msg), copy.deepcopy(msg)]

        to = get_msg_to(conversation)

        self.assertEqual(to, ["GROUP"])

    def test_get_msg_to_returns_newest_internal_user_if_known(self):
        msg = {"something": "somethings"}
        first_message_with_user = {"internal_user": "user1", "from_internal": True}
        second_message_with_user = {"internal_user": "user2", "from_internal": True}

        conversation = [msg, first_message_with_user, second_message_with_user, copy.deepcopy(msg)]

        to = get_msg_to(conversation)

        self.assertEqual(to, ["user2"])

    @requests_mock.mock()
    def test_get_msg_without_survey_name(self, mock_request):
        mock_request.get(url_get_thread, json={"messages": [message_json], "is_closed": False})
        mock_request.get(url_get_conversation_count, json={"total": 0})
        mock_request.get(url_get_survey_long_name, json={"longName": None})
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get("secure-message/threads/9e3465c0-9172-4974-a7d1-3a01592d1594")
        self.assertTrue("Survey: ".encode() in response.data)
        self.assertTrue("No Survey".encode() in response.data)

    @requests_mock.mock()
    def test_get_msg_without_business_name(self, mock_request):
        message_without_business = copy.deepcopy(message_json)
        del message_without_business["@business_details"]["name"]
        mock_request.get(url_get_thread, json={"messages": [message_without_business], "is_closed": False})
        mock_request.get(url_get_conversation_count, json={"total": 0})
        mock_request.get(url_get_survey_long_name, json={"longName": None})
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get("secure-message/threads/9e3465c0-9172-4974-a7d1-3a01592d1594")
        self.assertTrue("Business:".encode() in response.data)
        self.assertTrue("No Business".encode() in response.data)
