import json
import logging

from flask import current_app as app
from redis.exceptions import RedisError
from structlog import wrap_logger

from frontstage import redis
from frontstage.controllers.collection_instrument_controller import (
    get_collection_instrument,
)

logger = wrap_logger(logging.getLogger(__name__))


class RedisCache:
    COLLECTION_INSTRUMENT_CATEGORY_EXPIRY = 600  # 10 mins
    COLLECTION_EXERCISE_CATEGORY_EXPIRY = 600  # 10 mins

    def get_collection_instrument(self, key):
        """
        Gets the collection-instrument from redis or the collection-instrument service

        :param key: Key in redis (for this example will be a frontstage:collection-instrument:id)
        :return: Result from either the cache or collection instrument service
        """
        redis_key = f"frontstage:collection-instrument:{key}"
        try:
            result = redis.get(redis_key)
        except RedisError:
            logger.error("Error getting value from cache, please investigate", key=redis_key, exc_info=True)
            result = None

        if not result:
            logger.info("Key not in cache, getting value from collection instrument service", key=redis_key)
            result = get_collection_instrument(key, app.config["COLLECTION_INSTRUMENT_URL"], app.config["BASIC_AUTH"])
            self.save(redis_key, result, self.COLLECTION_INSTRUMENT_CATEGORY_EXPIRY)
            return result

        return json.loads(result.decode("utf-8"))

    @staticmethod
    def save(key, value, expiry):
        if not expiry:
            logger.error("Expiry must be provided")
            raise ValueError("Expiry must be provided")
        try:
            redis.set(key, json.dumps(value), ex=expiry)
        except RedisError:
            # Not bubbling the exception up as not being able to save to the cache isn't fatal, it'll just impact
            # performance
            logger.error("Error saving key, please investigate", key=key, exc_info=True)
