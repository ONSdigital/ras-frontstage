from unittest import TestCase
from unittest.mock import patch
from frontstage import app

TESTMSG = b'THIS IS A TEST MESSAGE'


class TestAvailabilityMessage(TestCase):

    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    @patch('redis.StrictRedis.keys')
    @patch('redis.StrictRedis.get')
    def test_message_does_not_show_if_redis_flag_not_set(self, mock_redis_get, mock_redis_keys):
        mock_redis_get.return_value = b''
        mock_redis_keys.return_value = []
        response = self.app.get('/', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(TESTMSG in response.data)

    @patch('redis.StrictRedis.keys')
    @patch('redis.StrictRedis.get')
    def test_message_shows_correct_message_if_redis_flag_set(self, mock_redis_get, mock_redis_keys):
        mock_redis_get.return_value = TESTMSG
        mock_redis_keys.return_value = ['AVAILABILITY_MESSAGE']

        response = self.app.get('/', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(TESTMSG in response.data)
