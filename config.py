import os


# To choose which config to use when running frontstage set environment variable APP_SETTINGS to the name of the
# config object e.g. for the dev config set APP_SETTINGS=DevelopmentConfig
class Config(object):
    DEBUG = False
    TESTING = False
    VERSION = '0.4.7'
    PORT = os.getenv('PORT', 8082)
    MAX_UPLOAD_LENGTH = os.getenv('MAX_UPLOAD_LENGTH', 20 * 1024 * 1024)

    SECRET_KEY = os.getenv('SECRET_KEY')
    SECURITY_USER_NAME = os.getenv('SECURITY_USER_NAME')
    SECURITY_USER_PASSWORD = os.getenv('SECURITY_USER_PASSWORD')
    BASIC_AUTH = (SECURITY_USER_NAME, SECURITY_USER_PASSWORD)
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_SECRET = os.getenv('JWT_SECRET')
    VALIDATE_JWT = os.environ.get('VALIDATE_JWT', True)
    GOOGLE_ANALYTICS = os.getenv('GOOGLE_ANALYTICS', None)
    GOOGLE_TAG_MANAGER = os.getenv('GOOGLE_TAG_MANAGER', None)
    NON_DEFAULT_VARIABLES = ['SECRET_KEY', 'SECURITY_USER_NAME', 'SECURITY_USER_PASSWORD', 'JWT_SECRET']
    AVAILABILITY_BANNER = os.getenv('AVAILABILITY_BANNER', False)
    
    ACCOUNT_SERVICE_URL = os.getenv('ACCOUNT_SERVICE_URL')
    EQ_URL = os.getenv('EQ_URL')
    JSON_SECRET_KEYS = os.getenv('JSON_SECRET_KEYS')

    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = os.getenv('REDIS_PORT', 6379)
    REDIS_DB = os.getenv('REDIS_DB', 1)

    PASSWORD_MATCH_ERROR_TEXT = 'Your passwords do not match'
    PASSWORD_CRITERIA_ERROR_TEXT = 'Your password doesn\'t meet the requirements'
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 160

    CASE_URL = os.getenv('CASE_URL')
    CASE_USERNAME = os.getenv('CASE_USERNAME')
    CASE_PASSWORD = os.getenv('CASE_PASSWORD')
    CASE_AUTH = (CASE_USERNAME, CASE_PASSWORD)

    COLLECTION_EXERCISE_URL = os.getenv('COLLECTION_EXERCISE_URL')
    COLLECTION_EXERCISE_USERNAME = os.getenv('COLLECTION_EXERCISE_USERNAME')
    COLLECTION_EXERCISE_PASSWORD = os.getenv('COLLECTION_EXERCISE_PASSWORD')
    COLLECTION_EXERCISE_AUTH = (COLLECTION_EXERCISE_USERNAME, COLLECTION_EXERCISE_PASSWORD)

    COLLECTION_INSTRUMENT_URL = os.getenv('COLLECTION_INSTRUMENT_URL')
    COLLECTION_INSTRUMENT_USERNAME = os.getenv('COLLECTION_INSTRUMENT_USERNAME')
    COLLECTION_INSTRUMENT_PASSWORD = os.getenv('COLLECTION_INSTRUMENT_PASSWORD')
    COLLECTION_INSTRUMENT_AUTH = (COLLECTION_INSTRUMENT_USERNAME, COLLECTION_INSTRUMENT_PASSWORD)

    IAC_URL = os.getenv('IAC_URL')
    IAC_USERNAME = os.getenv('IAC_USERNAME')
    IAC_PASSWORD = os.getenv('IAC_PASSWORD')
    IAC_AUTH = (IAC_USERNAME, IAC_PASSWORD)

    OAUTH_URL = os.getenv('OAUTH_URL')
    OAUTH_CLIENT_ID = os.getenv('OAUTH_CLIENT_ID')
    OAUTH_CLIENT_SECRET = os.getenv('OAUTH_CLIENT_SECRET')
    OAUTH_BASIC_AUTH = (OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET)
    
    PARTY_URL = os.getenv('PARTY_URL')
    PARTY_USERNAME = os.getenv('PARTY_USERNAME')
    PARTY_PASSWORD = os.getenv('PARTY_PASSWORD')
    PARTY_AUTH = (PARTY_USERNAME, PARTY_PASSWORD)

    SECURE_MESSAGE_URL = os.getenv('SECURE_MESSAGE_URL')

    SURVEY_URL = os.getenv('SURVEY_URL')
    SURVEY_USERNAME = os.getenv('SURVEY_USERNAME')
    SURVEY_PASSWORD = os.getenv('SURVEY_PASSWORD')
    SURVEY_AUTH = (SURVEY_USERNAME, SURVEY_PASSWORD)


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    SECRET_KEY = os.getenv('SECRET_KEY', 'ONS_DUMMY_KEY')
    JWT_SECRET = os.getenv('JWT_SECRET', 'testsecret')

    SECURITY_USER_NAME = os.getenv('SECURITY_USER_NAME', 'admin')
    SECURITY_USER_PASSWORD = os.getenv('SECURITY_USER_PASSWORD', 'secret')
    BASIC_AUTH = (SECURITY_USER_NAME, SECURITY_USER_PASSWORD)

    ACCOUNT_SERVICE_URL = os.getenv('ACCOUNT_SERVICE_URL', 'http://localhost:8082/surveys/todo')
    EQ_URL = os.getenv('EQ_URL', 'https://localhost:5000/session?token=')
    JSON_SECRET_KEYS = os.getenv('JSON_SECRET_KEYS') or open("./tests/test_data/jwt-test-keys/test_key.json").read()

    CASE_URL = os.getenv('CASE_URL', 'http://localhost:8171')
    CASE_USERNAME = os.getenv('CASE_USERNAME', 'admin')
    CASE_PASSWORD = os.getenv('CASE_PASSWORD', 'secret')
    CASE_AUTH = (CASE_USERNAME, CASE_PASSWORD)

    COLLECTION_EXERCISE_URL = os.getenv('COLLECTION_EXERCISE_URL', 'http://localhost:8145')
    COLLECTION_EXERCISE_USERNAME = os.getenv('COLLECTION_EXERCISE_USERNAME', 'admin')
    COLLECTION_EXERCISE_PASSWORD = os.getenv('COLLECTION_EXERCISE_PASSWORD', 'secret')
    COLLECTION_EXERCISE_AUTH = (COLLECTION_EXERCISE_USERNAME, COLLECTION_EXERCISE_PASSWORD)

    COLLECTION_INSTRUMENT_URL = os.getenv('COLLECTION_INSTRUMENT_URL', 'http://localhost:8002')
    COLLECTION_INSTRUMENT_USERNAME = os.getenv('COLLECTION_INSTRUMENT_USERNAME', 'admin')
    COLLECTION_INSTRUMENT_PASSWORD = os.getenv('COLLECTION_INSTRUMENT_PASSWORD', 'secret')
    COLLECTION_INSTRUMENT_AUTH = (COLLECTION_INSTRUMENT_USERNAME, COLLECTION_INSTRUMENT_PASSWORD)

    IAC_URL = os.getenv('IAC_URL', 'http://localhost:8121')
    IAC_USERNAME = os.getenv('IAC_USERNAME', 'admin')
    IAC_PASSWORD = os.getenv('IAC_PASSWORD', 'secret')
    IAC_AUTH = (IAC_USERNAME, IAC_PASSWORD)

    OAUTH_URL = os.getenv('OAUTH_URL', 'http://localhost:8040')
    OAUTH_CLIENT_ID = os.getenv('OAUTH_CLIENT_ID', 'ons@ons.gov')
    OAUTH_CLIENT_SECRET = os.getenv('OAUTH_CLIENT_SECRET', 'password')
    OAUTH_BASIC_AUTH = (OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET)

    PARTY_URL = os.getenv('PARTY_URL', 'http://localhost:8081')
    PARTY_USERNAME = os.getenv('PARTY_USERNAME', 'admin')
    PARTY_PASSWORD = os.getenv('PARTY_PASSWORD', 'secret')
    PARTY_AUTH = (PARTY_USERNAME, PARTY_PASSWORD)

    SECURE_MESSAGE_URL = os.getenv('SECURE_MESSAGE_URL', 'http://localhost:5050')

    SURVEY_URL = os.getenv('SURVEY_URL', 'http://localhost:8080')
    SURVEY_USERNAME = os.getenv('SURVEY_USERNAME', 'admin')
    SURVEY_PASSWORD = os.getenv('SURVEY_PASSWORD', 'secret')
    SURVEY_AUTH = (SURVEY_USERNAME, SURVEY_PASSWORD)


class TestingConfig(DevelopmentConfig):
    TESTING = True
    DEVELOPMENT = False
    WTF_CSRF_ENABLED = False
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    JWT_SECRET = 'testsecret'
    REDIS_DB = os.getenv('REDIS_DB', 13)
    ACCOUNT_SERVICE_URL = 'http://frontstage-url/surveys'
    EQ_URL = 'https://eq-test/session?token='
    JSON_SECRET_KEYS = open("./tests/test_data/jwt-test-keys/test_key.json").read()
