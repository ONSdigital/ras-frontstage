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
        redis_get.return_value = b'{"type": "SEFT"}'
        with app.app_context():
            cache = RedisCache()
            result = cache.get_collection_instrument(test_uuid)
            self.assertEqual(result, {"type": "SEFT"})

    @patch("redis.StrictRedis.get")
    def test_get_not_in_cache(self, redis_get):
        redis_get.return_value = None
        ci_response = {"type": "SEFT"}
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                f"http://localhost:8002/collection-instrument-api/1.0.2/{test_uuid}",
                json=ci_response,
                status=200,
                content_type="application/json",
            )
            with app.app_context():
                cache = RedisCache()
                result = cache.get_collection_instrument(test_uuid)
                self.assertEqual(result, {"type": "SEFT"})
