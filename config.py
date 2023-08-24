import os

# To choose which config to use when running frontstage set environment variable APP_SETTINGS to the name of the
# config object e.g. for the dev config set APP_SETTINGS=DevelopmentConfig
from distutils.util import strtobool


class Config(object):
    DEBUG = False
    TESTING = False
    PREFERRED_URL_SCHEME = "https"
    PORT = os.getenv("PORT", 8082)
    MAX_UPLOAD_LENGTH = os.getenv("MAX_UPLOAD_LENGTH", 20 * 1024 * 1024)
    LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")

    EMAIL_TOKEN_SALT = os.getenv("EMAIL_TOKEN_SALT", "aardvark")
    EMAIL_TOKEN_EXPIRY = int(os.getenv("EMAIL_TOKEN_EXPIRY", "86400"))

    SECRET_KEY = os.getenv("SECRET_KEY")
    SECURITY_USER_NAME = os.getenv("SECURITY_USER_NAME")
    SECURITY_USER_PASSWORD = os.getenv("SECURITY_USER_PASSWORD")
    BASIC_AUTH = (SECURITY_USER_NAME, SECURITY_USER_PASSWORD)
    JWT_SECRET = os.getenv("JWT_SECRET")
    GOOGLE_ANALYTICS_MEASUREMENT_ID = os.getenv("GOOGLE_ANALYTICS_MEASUREMENT_ID")
    GOOGLE_TAG_MANAGER_ID = os.getenv("GOOGLE_TAG_MANAGER_ID")
    NON_DEFAULT_VARIABLES = ["SECRET_KEY", "SECURITY_USER_NAME", "SECURITY_USER_PASSWORD", "JWT_SECRET"]

    BANNER_SERVICE_HOST = os.getenv("BANNER_API_SERVICE_HOST", "http://localhost")
    BANNER_SERVICE_PORT = os.getenv("BANNER_API_SERVICE_PORT", "8000")
    BANNER_SERVICE_URL = os.getenv("BANNER_SERVICE_URL", f"{BANNER_SERVICE_HOST}:{BANNER_SERVICE_PORT}")

    ACCESS_CONTROL_ALLOW_ORIGIN = os.getenv("ACCESS_CONTROL_ALLOW_ORIGIN", "*")
    ACCOUNT_SERVICE_URL = os.getenv("ACCOUNT_SERVICE_URL")
    ACCOUNT_SERVICE_LOG_OUT_URL = os.getenv("ACCOUNT_SERVICE_LOG_OUT_URL")
    EQ_URL = os.getenv("EQ_URL")
    EQ_V3_URL = os.getenv("EQ_V3_URL")
    JSON_SECRET_KEYS = os.getenv("JSON_SECRET_KEYS")

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = os.getenv("REDIS_PORT", 6379)
    REDIS_DB = os.getenv("REDIS_DB", 1)

    PASSWORD_MATCH_ERROR_TEXT = "Your passwords do not match"
    PASSWORD_CRITERIA_ERROR_TEXT = "Your password doesn't meet the requirements"
    PASSWORD_MIN_LENGTH = 12
    PASSWORD_MAX_LENGTH = 160
    PASSWORD_RESET_ATTEMPTS_TIMEOUT = int(os.getenv("PASSWORD_RESET_ATTEMPTS_TIMEOUT", "86400"))

    AUTH_URL = os.getenv("AUTH_URL")
    CASE_URL = os.getenv("CASE_URL")
    COLLECTION_EXERCISE_URL = os.getenv("COLLECTION_EXERCISE_URL")
    COLLECTION_INSTRUMENT_URL = os.getenv("COLLECTION_INSTRUMENT_URL")
    IAC_URL = os.getenv("IAC_URL")
    PARTY_URL = os.getenv("PARTY_URL")
    SECURE_MESSAGE_URL = os.getenv("SECURE_MESSAGE_URL")
    SURVEY_URL = os.getenv("SURVEY_URL")

    EMAIL_MATCH_ERROR_TEXT = "Your email addresses do not match"

    RAS_NOTIFY_REQUEST_PASSWORD_CHANGE_TEMPLATE = os.getenv(
        "RAS_NOTIFY_REQUEST_PASSWORD_CHANGE_TEMPLATE", "request_password_change_id"
    )
    SEND_EMAIL_TO_GOV_NOTIFY = os.getenv("SEND_EMAIL_TO_GOV_NOTIFY", False)
    REQUESTS_POST_TIMEOUT = os.getenv("REQUESTS_POST_TIMEOUT", 20)
    SECURE_APP = bool(strtobool(os.getenv("SECURE_APP", "True")))
    # WTF_CSRF_ENABLED is used by the flask_wtf.csrf library to control if CSRF protection is turned on
    WTF_CSRF_ENABLED = bool(strtobool(os.getenv("WTF_CSRF_ENABLED", str(SECURE_APP))))
    WTF_CSRF_TIME_LIMIT = int(os.getenv("WTF_CSRF_TIME_LIMIT", "7200"))

    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "ras-rm-sandbox")
    PUBSUB_TOPIC = os.getenv("PUBSUB_TOPIC", "ras-rm-notify-test")

    # In preprod and prod, this project will point to the SDX project as they own the topic.  In dev environments
    # this will be our ras-rm project as we create the topic ourselves.
    SEFT_UPLOAD_PROJECT = os.getenv("SEFT_UPLOAD_PROJECT", "ras-rm-sandbox")
    SEFT_UPLOAD_PUBSUB_TOPIC = os.getenv("SEFT_UPLOAD_PUBSUB_TOPIC", "ras-rm-notify-test")
    SEFT_UPLOAD_BUCKET_NAME = os.getenv("SEFT_UPLOAD_BUCKET_NAME", "test-bucket")
    # Prefix only used for dev environments to file in folders within the bucket
    SEFT_UPLOAD_BUCKET_FILE_PREFIX = os.getenv("SEFT_UPLOAD_BUCKET_FILE_PREFIX")
    ONS_GNU_RECIPIENT = os.getenv("ONS_GNU_RECIPIENT")
    ONS_GNU_FINGERPRINT = os.getenv("ONS_GNU_FINGERPRINT")
    ONS_GNU_PUBLIC_CRYPTOKEY = os.getenv("ONS_GNU_PUBLIC_CRYPTOKEY")

    CANARY_GENERATE_ERRORS = bool(strtobool(os.getenv("CANARY_GENERATE_ERRORS", "False")))
    MAX_SHARED_SURVEY = int(os.getenv("MAX_SHARED_SURVEY", "50"))
    UNDER_MAINTENANCE = bool(strtobool(os.getenv("UNDER_MAINTENANCE", "False")))


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    PREFERRED_URL_SCHEME = "http"
    SECRET_KEY = os.getenv("SECRET_KEY", "ONS_DUMMY_KEY")
    JWT_SECRET = os.getenv("JWT_SECRET", "testsecret")
    LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "DEBUG")

    SECURITY_USER_NAME = os.getenv("SECURITY_USER_NAME", "admin")
    SECURITY_USER_PASSWORD = os.getenv("SECURITY_USER_PASSWORD", "secret")
    BASIC_AUTH = (SECURITY_USER_NAME, SECURITY_USER_PASSWORD)

    ACCOUNT_SERVICE_URL = os.getenv("ACCOUNT_SERVICE_URL", "http://localhost:8082/surveys/todo")
    ACCOUNT_SERVICE_LOG_OUT_URL = os.getenv("ACCOUNT_SERVICE_LOG_OUT_URL", "http://localhost:8082/sign-in/logout")
    EQ_URL = os.getenv("EQ_URL", "http://localhost:8086/session?token=")
    EQ_V3_URL = os.getenv("EQ_V3_URL", "http://localhost:8086/v3/session?token=")
    JSON_SECRET_KEYS = os.getenv("JSON_SECRET_KEYS") or open("./tests/test_data/jwt-test-keys/test_key.json").read()

    AUTH_URL = os.getenv("AUTH_URL", "http://localhost:8041")
    CASE_URL = os.getenv("CASE_URL", "http://localhost:8171")
    COLLECTION_EXERCISE_URL = os.getenv("COLLECTION_EXERCISE_URL", "http://localhost:8145")
    COLLECTION_INSTRUMENT_URL = os.getenv("COLLECTION_INSTRUMENT_URL", "http://localhost:8002")
    IAC_URL = os.getenv("IAC_URL", "http://localhost:8121")
    PARTY_URL = os.getenv("PARTY_URL", "http://localhost:8081")
    SECURE_MESSAGE_URL = os.getenv("SECURE_MESSAGE_URL", "http://localhost:5050")
    SURVEY_URL = os.getenv("SURVEY_URL", "http://localhost:8080")

    WTF_CSRF_TIME_LIMIT = int(os.getenv("WTF_CSRF_TIME_LIMIT", "3200"))
    SECURE_APP = bool(strtobool(os.getenv("SECURE_APP", "False")))


class TestingConfig(DevelopmentConfig):
    TESTING = True
    DEVELOPMENT = False
    WTF_CSRF_ENABLED = False
    SEND_EMAIL_TO_GOV_NOTIFY = True
    EMAIL_TOKEN_SALT = "bulbous"
    JWT_SECRET = "testsecret"
    REDIS_DB = os.getenv("REDIS_DB", 13)
    ACCOUNT_SERVICE_URL = "http://frontstage-url/surveys"
    ACCOUNT_SERVICE_LOG_OUT_URL = "http://frontstage-url/sign-in/logout"
    EQ_URL = "https://eq-test/session?token="
    EQ_V3_URL = "https://eq-test/v3/session?token="
    JSON_SECRET_KEYS = open("./tests/test_data/jwt-test-keys/test_key.json").read()
    SECURITY_USER_NAME = "username"
    SECURITY_USER_PASSWORD = "password"
    SECRET_KEY = os.getenv("SECRET_KEY", "ONS_DUMMY_KEY")
    REQUESTS_POST_TIMEOUT = 99
    WTF_CSRF_TIME_LIMIT = int(os.getenv("WTF_CSRF_TIME_LIMIT", "3200"))
    PASSWORD_RESET_ATTEMPTS_TIMEOUT = int(os.getenv("PASSWORD_RESET_ATTEMPTS_TIMEOUT", "5"))
    SECURE_APP = bool(strtobool(os.getenv("SECURE_APP", "False")))
    ACCESS_CONTROL_ALLOW_ORIGIN = os.getenv("ACCESS_CONTROL_ALLOW_ORIGIN", "http://localhost")
    UNDER_MAINTENANCE = bool(strtobool(os.getenv("UNDER_MAINTENANCE", "False")))
