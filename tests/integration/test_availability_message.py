from unittest import TestCase
from unittest.mock import patch
from frontstage import app

import requests_mock
from tests.integration.mocked_services import url_banner_api

TESTMSG = 'THIS IS A TEST MESSAGE'


class TestAvailabilityMessage(TestCase):

    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    @requests_mock.mock()
    def test_message_does_not_show_no_banner_set(self, mock_request):
        mock_request.get(url_banner_api, status_code=404)
        response = self.app.get('/', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(TESTMSG.encode() in response.data)

    @requests_mock.mock()
    def test_message_shows_correct_message_banner_is_set(self, mock_request):
        mock_request.get(url_banner_api, status_code=200, json={"id": "active", "content": TESTMSG})

        response = self.app.get('/', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(TESTMSG.encode() in response.data)
