from flask_wtf.csrf import CSRFProtect
import redis

from frontstage.create_app import create_app_object


app = create_app_object()
redis = redis.StrictRedis(host=app.config['REDIS_HOST'],
                          port=app.config['REDIS_PORT'],
                          db=app.config['REDIS_DB'])
csrf = CSRFProtect(app)

# Bind routes to app
import frontstage.views  # NOQA  # pylint: disable=wrong-import-position
import frontstage.error_handlers  # NOQA  # pylint: disable=wrong-import-position
