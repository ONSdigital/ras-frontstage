import json
import logging

from flask import current_app as app
from structlog import wrap_logger

from frontstage import redis
from frontstage.controllers.survey_controller import get_survey

logger = wrap_logger(logging.getLogger(__name__))


class RedisCache:
    def get(self, category, key):
        """
        Gets the key from redis

        :param category: A category to roughly describe what the key is for (e.g., survey, case, respondent)
        :param key: Key in redis (for this example will be a frontstage:survey id)
        :return:
        """
        redis_key = f"frontstage:{category}:{key}"
        logger.info("Seeing if it's in the cache", key=key, redis_key=redis_key)
        result = redis.get(redis_key)
        if not result:
            logger.info("Result not in cache", key=key, redis_key=redis_key)
            result = get_survey(app.config["SURVEY_URL"], app.config["BASIC_AUTH"], key)
            self.save(redis_key, result)
            return result
        logger.info("It's in the cache, returning", key=key)
        return json.loads(result.decode("utf-8"))

    def save(self, key, value):
        logger.info("Saving result to cache")
        # TODO make expiry configurable,
        redis.set(key, json.dumps(value), ex=60)
