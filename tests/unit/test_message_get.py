import copy
import unittest
import requests_mock
from unittest.mock import patch

from frontstage import app
from frontstage.views.secure_messaging.message_get import get_msg_to
from tests.integration.mocked_services import (message_json, url_get_conversation_count,
                                               url_get_thread, url_get_survey_long_name,
                                               encoded_jwt_token)

class TestMessageGet(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.set_cookie('localhost', 'authorization', 'session_key')
        self.patcher = patch('redis.StrictRedis.get', return_value=encoded_jwt_token)
        self.patcher.start()
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54" # NOQA
        }

    def test_get_msg_to_returns_group_if_no_internal_user(self):
        msg = {'something': 'somethings'}
        conversation = [msg, copy.deepcopy(msg), copy.deepcopy(msg)]

        to = get_msg_to(conversation)

        self.assertEqual(to, ['GROUP'])

    def test_get_msg_to_returns_newest_internal_user_if_known(self):
        msg = {'something': 'somethings'}
        first_message_with_user = {'internal_user': 'user1', 'from_internal': True}
        second_message_with_user = {'internal_user': 'user2', 'from_internal': True}

        conversation = [msg, first_message_with_user, second_message_with_user, copy.deepcopy(msg)]

        to = get_msg_to(conversation)

        self.assertEqual(to, ['user2'])

    @requests_mock.mock()
    def test_get_msg_without_survey_name(self, mock_request):
        mock_request.get(url_get_thread, json={'messages': [message_json], 'is_closed': False})
        mock_request.get(url_get_conversation_count, json={'total': 0})
        mock_request.get(url_get_survey_long_name, json={"longName": "None",})
        response = self.app.get("secure-message/threads/9e3465c0-9172-4974-a7d1-3a01592d1594")
        self.assertTrue('None'.encode() in response.data)
