import unittest

import requests_mock

from frontstage import app
from frontstage.common.api_call import api_call
from frontstage.exceptions.exceptions import InvalidRequestMethod


class TestApiCall(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.test_url = 'http://localhost:8083/test_endpoint'
        self.test_url_with_params = 'http://localhost:8083/test_endpoint?param=param'

    @requests_mock.mock()
    def test_api_call_get_success(self, mock_request):
        mock_request.get(self.test_url, status_code=200)

        response = api_call('GET', 'test_endpoint')

        self.assertEqual(response.status_code, 200)

    @requests_mock.mock()
    def test_api_call_post_success(self, mock_request):
        mock_request.post(self.test_url, status_code=200)

        response = api_call('POST', 'test_endpoint')

        self.assertEqual(response.status_code, 200)

    @requests_mock.mock()
    def test_api_call_put_success(self, mock_request):
        mock_request.put(self.test_url, status_code=200)

        response = api_call('PUT', 'test_endpoint')

        self.assertEqual(response.status_code, 200)

    def test_api_call_invalid_method(self):
        with self.assertRaises(InvalidRequestMethod):
            api_call('GOT', 'test_endpoint')

    @requests_mock.mock()
    def test_api_call_get_success_with_params(self, mock_request):
        mock_request.get(self.test_url_with_params, status_code=200)

        response = api_call('GET', 'test_endpoint', {"param": "param"})

        self.assertEqual(response.status_code, 200)
