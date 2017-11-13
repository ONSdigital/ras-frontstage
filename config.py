import os


# To choose which config to use when running frontstage set environment variable APP_SETTINGS to the name of the
# config object e.g. for the dev config set APP_SETTINGS=DevelopmentConfig
class Config(object):
    DEBUG = False
    TESTING = False
    NAME = os.getenv('NAME', 'ras-frontstage')
    VERSION = os.getenv('VERSION', '0.2.0')
    MAX_UPLOAD_LENGTH = os.getenv('MAX_UPLOAD_LENGTH',  20 * 1024 * 1024)

    WTF_CSRF_ENABLED = os.getenv('WTF_CSRF_ENABLED', True)
    SECRET_KEY = os.getenv('SECRET_KEY')
    SECURITY_USER_NAME = os.getenv('SECURITY_USER_NAME')
    SECURITY_USER_PASSWORD = os.getenv('SECURITY_USER_PASSWORD')
    BASIC_AUTH = (SECURITY_USER_NAME, SECURITY_USER_PASSWORD)
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_SECRET = os.getenv('JWT_SECRET')
    VALIDATE_JWT = os.environ.get('VALIDATE_JWT', True)
    GOOGLE_ANALYTICS = os.getenv('GOOGLE_ANALYTICS', None)
    SELENIUM_TEST_URL = os.environ.get('SELENIUM_TEST_URL', 'http://localhost:8080')
    NON_DEFAULT_VARIABLES = ['SECRET_KEY', 'SECURITY_USER_NAME', 'SECURITY_USER_PASSWORD', 'JWT_SECRET']

    PASSWORD_MATCH_ERROR_TEXT = 'Your passwords do not match'
    PASSWORD_CRITERIA_ERROR_TEXT = 'Your password doesn\'t meet the requirements'
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_MAX_LENGTH = 160

    RAS_FRONTSTAGE_API_HOST = os.getenv('RAS_FRONTSTAGE_API_HOST', 'localhost')
    RAS_FRONTSTAGE_API_PORT = os.getenv('RAS_FRONTSTAGE_API_PORT', 8083)
    RAS_FRONTSTAGE_API_PROTOCOL = os.getenv('RAS_FRONTSTAGE_API_PROTOCOL', 'http')
    RAS_FRONTSTAGE_API_SERVICE = '{}://{}:{}/'.format(RAS_FRONTSTAGE_API_PROTOCOL,
                                                      RAS_FRONTSTAGE_API_HOST,
                                                      RAS_FRONTSTAGE_API_PORT)
    GET_MESSAGES_URL = 'messages_list'
    GET_MESSAGE_URL = 'message'
    SEND_MESSAGE_URL = 'send_message'

    SIGN_IN_URL = 'sign-in'

    REQUEST_PASSWORD_CHANGE = 'request_password_change'
    VERIFY_PASSWORD_TOKEN = 'verify_password_token'
    CHANGE_PASSWORD = 'change_password'

    VALIDATE_ENROLMENT = 'validate-enrolment'
    CONFIRM_ORGANISATION_SURVEY = 'confirm-organisation-survey'
    CREATE_ACCOUNT = 'create-account'
    VERIFY_EMAIL = 'verify-email'

    SURVEYS_LIST = 'surveys-list'
    ACCESS_CASE = 'access-case'
    DOWNLOAD_CI = 'download-ci'
    UPLOAD_CI = 'upload-ci'


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    SECRET_KEY = os.getenv('SECRET_KEY', 'ONS_DUMMY_KEY')
    JWT_SECRET = os.getenv('JWT_SECRET', 'vrwgLNWEffe45thh545yuby')
    SECURITY_USER_NAME = os.getenv('SECURITY_USER_NAME', 'test_user')
    SECURITY_USER_PASSWORD = os.getenv('SECURITY_USER_PASSWORD', 'test_password')
    BASIC_AUTH = (SECURITY_USER_NAME, SECURITY_USER_PASSWORD)


class TestingConfig(DevelopmentConfig):
    TESTING = True
    DEVELOPMENT = False
    WTF_CSRF_ENABLED = False
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
