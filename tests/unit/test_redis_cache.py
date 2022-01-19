import unittest
from unittest.mock import patch

import responses

from frontstage import app
from frontstage.common.redis_cache import RedisCache

test_uuid = "5d640989-e20d-4367-b341-f067e5343097"


class TestRedisCache(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    @patch("redis.StrictRedis.get")
    def test_get(self, redis_get):
        redis_get.return_value = b'{"shortName": "MBS"}'
        with app.app_context():
            cache = RedisCache()
            result = cache.get_survey(test_uuid)
            self.assertEqual(result, {"shortName": "MBS"})

    @patch("redis.StrictRedis.get")
    def test_get_not_in_cache(self, redis_get):
        redis_get.return_value = None
        survey_response = {"shortName": "MBS"}
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                f"http://localhost:8080/surveys/{test_uuid}",
                json=survey_response,
                status=200,
                content_type="application/json",
            )
            with app.app_context():
                cache = RedisCache()
                result = cache.get_survey(test_uuid)
                self.assertEqual(result, {"shortName": "MBS"})
