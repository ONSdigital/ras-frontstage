import json
import logging
from redis.exceptions import RedisError

from flask import current_app as app
from structlog import wrap_logger

from frontstage import redis
from frontstage.controllers.survey_controller import get_survey

logger = wrap_logger(logging.getLogger(__name__))


class RedisCache:
    SURVEY_CATEGORY_EXPIRY = 300  # 5 mins

    def get_survey(self, key):
        """
        Gets the key from redis

        :param key: Key in redis (for this example will be a frontstage:survey id)
        :return: Result from either the cache or survey service
        """
        redis_key = f"frontstage:survey:{key}"
        try:
            result = redis.get(redis_key)
        except RedisError:
            logger.error("Error getting value from cache, please investigate", key=redis_key, exc_info=True)
            result = None

        if not result:
            logger.info("Key not in cache, getting value from survey service", key=redis_key)
            result = get_survey(app.config["SURVEY_URL"], app.config["BASIC_AUTH"], key)
            self.save(redis_key, result)
            return result

        return json.loads(result.decode("utf-8"))

    def save(self, key, value):
        try:
            redis.set(key, json.dumps(value), ex=self.SURVEY_CATEGORY_EXPIRY)
        except RedisError:
            # Not bubbling the exception up as not being able to save to the cache isn't fatal, it'll just impact
            # performance
            logger.error("Error saving key, please investigate", key=key, exc_info=True)
