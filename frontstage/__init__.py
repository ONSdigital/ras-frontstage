import redis
from flask_wtf.csrf import CSRFProtect
from frontstage.create_app import create_app_object


app = create_app_object()
redis = redis.StrictRedis(host=app.config['REDIS_HOST'],
                          port=app.config['REDIS_PORT'],
                          db=app.config['REDIS_DB'])
csrf = CSRFProtect(app)


@app.context_processor
def inject_availability_message():
    if len(redis.keys('AVAILABILITY_MESSAGE')) == 1:
        return {
            "availability_message": redis.get('AVAILABILITY_MESSAGE').decode('utf-8')
            }
    return {}


# Bind routes to app
import frontstage.views  # NOQA  # pylint: disable=wrong-import-position
import frontstage.error_handlers  # NOQA  # pylint: disable=wrong-import-position
