from unittest import TestCase
from unittest.mock import patch
from frontstage import app

TESTMSG = b'THIS IS A TEST MESSAGE'


class TestAvailabilityMessage(TestCase):

    def setUp(self):
        app.testing = True
        self.app = app.test_client()

    @patch('redis.StrictRedis.get')
    def test_message_does_not_show_if_redis_flag_not_set(self, mock_redis_get):
        mock_redis_get.return_value = b''
        response = self.app.get('/', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(TESTMSG in response.data)

    @patch('redis.StrictRedis.get')
    def test_message_shows_correct_message_if_redis_flag_set(self, mock_redis_get):
        mock_redis_get.return_value = TESTMSG

        response = self.app.get('/', follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(TESTMSG in response.data)
