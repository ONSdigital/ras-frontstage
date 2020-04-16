import redis
from frontstage.create_app import create_app_object
from flask_talisman import Talisman

# TODO: review https://content-security-policy.com/, remove this comment if we're covered.
CSP_POLICY = {
    'default-src': ["'self'", 'https://cdn.ons.gov.uk'],
    'font-src': ["'self'", 'data:', 'https://fonts.gstatic.com', 'https://cdn.ons.gov.uk'],
    'script-src': ["'self'", 'https://www.googletagmanager.com', 'https://cdn.ons.gov.uk'],
    'connect-src': ["'self'", 'https://www.googletagmanager.com', 'https://tagmanager.google.com', 'https://cdn.ons.gov.uk'],
    'img-src': ["'self'", 'data:', 'https://www.gstatic.com', 'https://www.google-analytics.com',
                'https://www.googletagmanager.com', 'https://ssl.gstatic.com', 'https://cdn.ons.gov.uk'],
    'style-src': ["'self'", 'https://cdn.ons.gov.uk', "'unsafe-inline'", 'https://tagmanager.google.com', 'https://fonts.googleapis.com'],
}

app = create_app_object()
talisman = Talisman(
    app,
    content_security_policy=CSP_POLICY,
    content_security_policy_nonce_in=['script-src'],
    force_https=app.config['SECURE_APP'],
    strict_transport_security=True,
    strict_transport_security_max_age=31536000,
    frame_options='DENY')
redis = redis.StrictRedis(host=app.config['REDIS_HOST'],
                          port=app.config['REDIS_PORT'],
                          db=app.config['REDIS_DB'])


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
