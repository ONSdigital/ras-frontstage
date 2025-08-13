import json
import unittest
from unittest.mock import MagicMock, patch

import responses

from frontstage import app
from frontstage.common.redis_cache import RedisCache

test_uuid = "5d640989-e20d-4367-b341-f067e5343097"
test_form_type = "0001"


class TestRedisCache(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    @patch("redis.StrictRedis.get")
    @patch("frontstage.common.redis_cache.RedisCache.save")
    def test_collection_instrument_in_cache(self, redis_save, redis_get):
        redis_get.return_value = b'{"type": "SEFT"}'
        with app.app_context():
            cache = RedisCache()
            cache.get_collection_instrument(test_uuid)
            redis_save.assert_not_called()

    @patch("redis.StrictRedis.get")
    @patch("frontstage.common.redis_cache.RedisCache.save")
    def test__collection_instrument_not_in_cache(self, redis_save, redis_get):
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
                cache.get_collection_instrument(test_uuid)
                redis_save.assert_called()

    @patch("redis.StrictRedis.get")
    @patch("frontstage.common.redis_cache.RedisCache.save")
    def test_registry_instrument_in_cache(self, redis_save, redis_get):
        redis_return_value = {test_uuid: test_form_type}
        redis_get.return_value = bytes(json.dumps(redis_return_value), "utf-8")
        with app.app_context():
            cache = RedisCache()
            cache.get_registry_instrument(test_uuid, test_form_type)
            redis_save.assert_not_called()

    @patch("redis.StrictRedis.get")
    @patch("frontstage.common.redis_cache.RedisCache.save")
    def test_registry_instrument_not_in_cache_test(self, redis_save, redis_get):
        redis_get.return_value = None
        registry_response = json.dumps({"collection_exercise_id": test_uuid, "form_type": test_form_type})
        with responses.RequestsMock() as rsps:
            rsps.add(
                rsps.GET,
                f"{app.config["COLLECTION_INSTRUMENT_URL"]}"
                f"/collection-instrument-api/1.0.2/registry-instrument/exercise-id/"
                f"{test_uuid}/formtype/{test_form_type}",
                json=registry_response,
                status=200,
                content_type="application/json",
            )
            with app.app_context():
                cache = RedisCache()
                cache.get_registry_instrument(test_uuid, test_form_type)
                redis_save.assert_called_once()
