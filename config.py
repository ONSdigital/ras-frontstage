import logging
import os

from structlog import wrap_logger


logger = wrap_logger(logging.getLogger(__name__))


class Config(object):
    DEBUG = False
    TESTING = False
    NAME = os.getenv('NAME', 'ras-frontstage')
    VERSION = os.getenv('VERSION', '0.2.0')

    WTF_CSRF_ENABLED = os.getenv('WTF_CSRF_ENABLED', True)
    SECRET_KEY = os.getenv('SECRET_KEY')
    SECURITY_USER_NAME = os.getenv('SECURITY_USER_NAME')
    SECURITY_USER_PASSWORD = os.getenv('SECURITY_USER_PASSWORD')
    BASIC_AUTH = (SECURITY_USER_NAME, SECURITY_USER_PASSWORD)
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_SECRET = os.getenv('JWT_SECRET')
    RAS_FRONTSTAGE_CLIENT_ID = os.environ.get('RAS_FRONTSTAGE_CLIENT_ID')
    RAS_FRONTSTAGE_CLIENT_SECRET = os.environ.get('RAS_FRONTSTAGE_CLIENT_SECRET')
    VALIDATE_JWT = os.environ.get('VALIDATE_JWT', True)
    GOOGLE_ANALYTICS = os.getenv('GOOGLE_ANALYTICS', None)
    SELENIUM_TEST_URL = os.environ.get('SELENIUM_TEST_URL', 'http://localhost:8080')
    NON_DEFAULT_VARIABLES = ['SECRET_KEY', 'SECURITY_USER_NAME', 'SECURITY_USER_PASSWORD', 'JWT_SECRET',
                             'RAS_FRONTSTAGE_CLIENT_ID', 'RAS_FRONTSTAGE_CLIENT_SECRET']

    PASSWORD_MATCH_ERROR_TEXT = 'Your passwords do not match'
    PASSWORD_CRITERIA_ERROR_TEXT = 'Your password doesn\'t meet the requirements'
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 160

    # Configurations for external services
    RM_CASE_SERVICE_HOST = os.getenv('RM_CASE_SERVICE_HOST', 'localhost')
    RM_CASE_SERVICE_PORT = os.getenv('RM_CASE_SERVICE_PORT', 8171)
    RM_CASE_SERVICE_PROTOCOL = os.getenv('RM_CASE_SERVICE_PROTOCOL', 'http')
    RM_CASE_SERVICE = '{}://{}:{}/'.format(RM_CASE_SERVICE_PROTOCOL, RM_CASE_SERVICE_HOST, RM_CASE_SERVICE_PORT)
    RM_CASE_GET = '{}cases/{}'
    RM_CASE_GET_BY_PARTY = '{}cases/partyid/{}'
    RM_CASE_GET_BY_IAC = '{}cases/iac/{}'

    RAS_COLLECTION_INSTRUMENT_SERVICE_HOST = os.getenv('RAS_COLLECTION_INSTRUMENT_SERVICE_HOST', 'localhost')
    RAS_COLLECTION_INSTRUMENT_SERVICE_PORT = os.getenv('RAS_COLLECTION_INSTRUMENT_SERVICE_PORT', 8002)
    RAS_COLLECTION_INSTRUMENT_SERVICE_PROTOCOL = os.getenv('RAS_COLLECTION_INSTRUMENT_SERVICE_PROTOCOL', 'http')
    RAS_COLLECTION_INSTRUMENT_SERVICE = '{}://{}:{}/'.format(RAS_COLLECTION_INSTRUMENT_SERVICE_PROTOCOL,
                                                             RAS_COLLECTION_INSTRUMENT_SERVICE_HOST,
                                                             RAS_COLLECTION_INSTRUMENT_SERVICE_PORT)
    RAS_CI_UPLOAD = '{}collection-instrument-api/1.0.2/survey_responses/{}'
    RAS_CI_GET = '{}collection-instrument-api/1.0.2/collectioninstrument/id/{}'
    RAS_CI_DOWNLOAD = '{}collection-instrument-api/1.0.2/download/{}'

    RAS_API_GATEWAY_SERVICE_HOST = os.getenv('RAS_API_GATEWAY_SERVICE_HOST', 'localhost')
    RAS_API_GATEWAY_SERVICE_PORT = os.getenv('RAS_API_GATEWAY_SERVICE_PORT', 8080)
    RAS_API_GATEWAY_SERVICE_PROTOCOL = os.getenv('RAS_API_GATEWAY_SERVICE_PROTOCOL', 'http')
    RAS_API_GATEWAY_SERVICE = '{}://{}:{}/'.format(RAS_API_GATEWAY_SERVICE_PROTOCOL,
                                                   RAS_API_GATEWAY_SERVICE_HOST,
                                                   RAS_API_GATEWAY_SERVICE_PORT)
    RAS_AGGREGATOR_TODO = '{}api/1.0.0/surveys/todo/{}'

    RM_IAC_SERVICE_HOST = os.getenv('RM_IAC_SERVICE_HOST', 'localhost')
    RM_IAC_SERVICE_PORT = os.getenv('RM_IAC_SERVICE_PORT', 8121)
    RM_IAC_SERVICE_PROTOCOL = os.getenv('RM_IAC_SERVICE_PROTOCOL', 'http')
    RM_IAC_SERVICE = '{}://{}:{}/'.format(RM_IAC_SERVICE_PROTOCOL, RM_IAC_SERVICE_HOST, RM_IAC_SERVICE_PORT)
    RM_IAC_GET = '{}iacs/{}'

    RAS_PARTY_SERVICE_HOST = os.getenv('RAS_PARTY_SERVICE_HOST', 'localhost')
    RAS_PARTY_SERVICE_PORT = os.getenv('RAS_PARTY_SERVICE_PORT', 8081)
    RAS_PARTY_SERVICE_PROTOCOL = os.getenv('RAS_PARTY_SERVICE_PROTOCOL', 'http')
    RAS_PARTY_SERVICE = '{}://{}:{}/'.format(RAS_PARTY_SERVICE_PROTOCOL, RAS_PARTY_SERVICE_HOST, RAS_PARTY_SERVICE_PORT)
    RAS_PARTY_GET_BY_BUSINESS = '{}party-api/v1/businesses/id/{}'
    RAS_PARTY_GET_BY_RESPONDENT = '{}party-api/v1/respondents/id/{}'
    RAS_PARTY_POST_RESPONDENTS = '{}party-api/v1/respondents'
    RAS_PARTY_VERIFY_EMAIL = '{}party-api/v1/emailverification/{}'
    RAS_PARTY_GET_BY_EMAIL = '{}party-api/v1/respondents/email/{}'
    RAS_PARTY_RESEND_VERIFICATION = '{}party-api/v1/resend-verification-email/{}'

    RM_COLLECTION_EXERCISE_SERVICE_HOST = os.getenv('RM_COLLECTION_EXERCISE_SERVICE_HOST', 'localhost')
    RM_COLLECTION_EXERCISE_SERVICE_PORT = os.getenv('RM_COLLECTION_EXERCISE_SERVICE_PORT', 8145)
    RM_COLLECTION_EXERCISE_SERVICE_PROTOCOL = os.getenv('RM_COLLECTION_EXERCISE_SERVICE_PROTOCOL', 'http')
    RM_COLLECTION_EXERCISE_SERVICE = '{}://{}:{}/'.format(RM_COLLECTION_EXERCISE_SERVICE_PROTOCOL,
                                                          RM_COLLECTION_EXERCISE_SERVICE_HOST,
                                                          RM_COLLECTION_EXERCISE_SERVICE_PORT)
    RM_COLLECTION_EXERCISES_GET = '{}collectionexercises/{}'

    RM_SURVEY_SERVICE_HOST = os.getenv('RM_SURVEY_SERVICE_HOST', 'localhost')
    RM_SURVEY_SERVICE_PORT = os.getenv('RM_SURVEY_SERVICE_PORT', 8080)
    RM_SURVEY_SERVICE_PROTOCOL = os.getenv('RM_SURVEY_SERVICE_PROTOCOL', 'http')
    RM_SURVEY_SERVICE = '{}://{}:{}/'.format(RM_SURVEY_SERVICE_PROTOCOL, RM_SURVEY_SERVICE_HOST, RM_SURVEY_SERVICE_PORT)
    RM_SURVEY_GET = '{}surveys/{}'

    RAS_SECURE_MESSAGE_SERVICE_HOST = os.getenv('RAS_SECURE_MESSAGE_SERVICE_HOST', 'localhost')
    RAS_SECURE_MESSAGE_SERVICE_PORT = os.getenv('RAS_SECURE_MESSAGE_SERVICE_PORT', 5050)
    RAS_SECURE_MESSAGE_SERVICE_PROTOCOL = os.getenv('RAS_SECURE_MESSAGE_SERVICE_PROTOCOL', 'http')
    RAS_SECURE_MESSAGE_SERVICE = '{}://{}:{}/'.format(RAS_SECURE_MESSAGE_SERVICE_PROTOCOL,
                                                      RAS_SECURE_MESSAGE_SERVICE_HOST,
                                                      RAS_SECURE_MESSAGE_SERVICE_PORT)

    ONS_OAUTH_SERVICE_HOST = os.environ.get('ONS_OAUTH_HOST', 'ons-oauth2.cfapps.io')
    ONS_OAUTH_SERVICE_PORT = os.getenv('ONS_OAUTH_PORT', 80)
    ONS_OAUTH_SERVICE_PROTOCOL = os.environ.get('ONS_OAUTH_PROTOCOL', 'http')
    ONS_OAUTH_SERVICE = '{}://{}:{}/'.format(ONS_OAUTH_SERVICE_PROTOCOL, ONS_OAUTH_SERVICE_HOST, ONS_OAUTH_SERVICE_PORT)
    ONS_TOKEN = '{}api/v1/tokens/'.format(ONS_OAUTH_SERVICE)

    MESSAGE_LIMIT = os.getenv('MESSAGE_LIMIT', 1000)
    CREATE_MESSAGE_API_URL = RAS_SECURE_MESSAGE_SERVICE + 'message/send'
    MESSAGES_API_URL = RAS_SECURE_MESSAGE_SERVICE + 'messages?limit={}'.format(MESSAGE_LIMIT)
    MESSAGE_GET_URL = RAS_SECURE_MESSAGE_SERVICE + 'message/{}'
    MESSAGE_MODIFY_URL = RAS_SECURE_MESSAGE_SERVICE + 'message/{}/modify'
    DRAFT_SAVE_API_URL = RAS_SECURE_MESSAGE_SERVICE + 'draft/save'
    DRAFT_GET_API_URL = RAS_SECURE_MESSAGE_SERVICE + 'draft/{}'
    DRAFT_PUT_API_URL = RAS_SECURE_MESSAGE_SERVICE + 'draft/{}/modify'
    LABELS_GET_API_URL = RAS_SECURE_MESSAGE_SERVICE + 'labels?name=unread'
    THREAD_GET_API_URL = RAS_SECURE_MESSAGE_SERVICE + 'thread/{}'


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    SECRET_KEY = 'ONS_DUMMY_KEY'
    JWT_SECRET = 'vrwgLNWEffe45thh545yuby'
    SECURITY_USER_NAME = 'dummy_user'
    SECURITY_USER_PASSWORD = 'dummy_password'
    BASIC_AUTH = (SECURITY_USER_NAME, SECURITY_USER_PASSWORD)
    RAS_FRONTSTAGE_CLIENT_ID = 'ons@ons.gov'
    RAS_FRONTSTAGE_CLIENT_SECRET = 'password'


class TestingConfig(DevelopmentConfig):
    TESTING = True
    DEVELOPMENT = False
    WTF_CSRF_ENABLED = False
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
