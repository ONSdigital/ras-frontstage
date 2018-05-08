import os


# To choose which config to use when running frontstage set environment variable APP_SETTINGS to the name of the
# config object e.g. for the dev config set APP_SETTINGS=DevelopmentConfig
class Config(object):
    DEBUG = False
    TESTING = False
    VERSION = '0.4.0'
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
    NON_DEFAULT_VARIABLES = ['SECRET_KEY', 'SECURITY_USER_NAME', 'SECURITY_USER_PASSWORD', 'JWT_SECRET']
    AVAILABILITY_BANNER = os.getenv('AVAILABILITY_BANNER', False)

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

    OAUTH_URL = os.getenv('OAUTH_URL')
    OAUTH_CLIENT_ID = os.getenv('OAUTH_CLIENT_ID')
    OAUTH_CLIENT_SECRET = os.getenv('OAUTH_CLIENT_SECRET')
    OAUTH_BASIC_AUTH = (OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET)

    PARTY_URL = os.getenv('PARTY_URL')
    PARTY_USERNAME = os.getenv('PARTY_USERNAME')
    PARTY_PASSWORD = os.getenv('PARTY_PASSWORD')
    PARTY_AUTH = (PARTY_USERNAME, PARTY_PASSWORD)

    SURVEY_URL = os.getenv('SURVEY_URL')
    SURVEY_USERNAME = os.getenv('SURVEY_USERNAME')
    SURVEY_PASSWORD = os.getenv('SURVEY_PASSWORD')
    SURVEY_AUTH = (SURVEY_USERNAME, SURVEY_PASSWORD)

    FRONTSTAGE_API_URL = os.getenv('FRONTSTAGE_API_URL')
    SECURE_MESSAGE_URL = os.getenv('SECURE_MESSAGE_URL')

    REQUEST_PASSWORD_CHANGE = '/passwords/request-password-change'
    VERIFY_PASSWORD_TOKEN = '/passwords/verify-password-token'
    CHANGE_PASSWORD = '/passwords/change-password'

    VALIDATE_ENROLMENT = '/register/validate-enrolment'
    CONFIRM_ORGANISATION_SURVEY = '/register/confirm-organisation-survey'
    CREATE_ACCOUNT = '/register/create-account'
    VERIFY_EMAIL = '/register/verify-email'

    SURVEYS_LIST = '/surveys/surveys-list'
    ADD_SURVEY = '/surveys/add-survey'
    CONFIRM_ADD_ORGANISATION_SURVEY = '/surveys/add-survey/confirm-add-organisation-survey'
    GENERATE_EQ_URL = '/surveys/generate-eq-url'


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    SECRET_KEY = os.getenv('SECRET_KEY', 'ONS_DUMMY_KEY')
    JWT_SECRET = os.getenv('JWT_SECRET', 'testsecret')

    SECURITY_USER_NAME = os.getenv('SECURITY_USER_NAME', 'admin')
    SECURITY_USER_PASSWORD = os.getenv('SECURITY_USER_PASSWORD', 'secret')
    BASIC_AUTH = (SECURITY_USER_NAME, SECURITY_USER_PASSWORD)

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

    OAUTH_URL = os.getenv('OAUTH_URL', 'http://localhost:8040')
    OAUTH_CLIENT_ID = os.getenv('OAUTH_CLIENT_ID', 'ons@ons.gov')
    OAUTH_CLIENT_SECRET = os.getenv('OAUTH_CLIENT_SECRET', 'password')
    OAUTH_BASIC_AUTH = (OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET)

    PARTY_URL = os.getenv('PARTY_URL', 'http://localhost:8081')
    PARTY_USERNAME = os.getenv('PARTY_USERNAME', 'admin')
    PARTY_PASSWORD = os.getenv('PARTY_PASSWORD', 'secret')
    PARTY_AUTH = (PARTY_USERNAME, PARTY_PASSWORD)

    SURVEY_URL = os.getenv('SURVEY_URL', 'http://localhost:8080')
    SURVEY_USERNAME = os.getenv('SURVEY_USERNAME', 'admin')
    SURVEY_PASSWORD = os.getenv('SURVEY_PASSWORD', 'secret')
    SURVEY_AUTH = (SURVEY_USERNAME, SURVEY_PASSWORD)

    FRONTSTAGE_API_URL = os.getenv('FRONTSTAGE_API_URL', 'http://localhost:8083')
    SECURE_MESSAGE_URL = os.getenv('SECURE_MESSAGE_URL', 'http://localhost:5050')


class TestingConfig(DevelopmentConfig):
    TESTING = True
    DEVELOPMENT = False
    WTF_CSRF_ENABLED = False
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    JWT_SECRET = 'testsecret'
    REDIS_DB = os.getenv('REDIS_DB', 13)
