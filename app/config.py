"""
This module hosts the config setup for our project
"""

import os
import logging


# ENV VARIABLES BELOW, SET THESE ON YOUR TERMINAL
# export APP_SETTINGS=config.Config
# export FLASK_APP=application.py
# export OAUTHLIB_INSECURE_TRANSPORT=1

# Default values
if "APP_SETTINGS" not in os.environ:
    os.environ["APP_SETTINGS"] = "config.Config"


class Config(object):
    """
    Base config class
    """
    DEBUG = False
    TESTING = False
    # CSRF_ENABLED = True
    CSRF_ENABLED = False
    # WTF_CSRF_CHECK_DEFAULT = False
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'this-really-needs-to-be-changed'
    dbname = "ras_frontstage_backup"
    # SQLALCHEMY_DATABASE_URI = "postgresql://" + dbname + ":password@localhost:5431/postgres"
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'postgresql://ras_frontstage_backup:password@localhost:5431/postgres')


class ProductionConfig(Config):
    """
    Production config class
    """
    DEBUG = False


class StagingConfig(Config):
    """
    Staging config class
    """
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    """
    Development config class
    """
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    """
    Testing config class
    """
    TESTING = True
    DEBUG = True
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    SQLALCHEMY_TRACK_MODIFICATIONS = True



class PartyService(Config):
    """
    This class is used to configure details and parameters for the PartyService microservice.
    This is temporary until an admin config feature is added to allow manual config of the microservice and/or a
    configuration management process
    """

    PARTYSERVICE_PROTOCOL = os.environ.get('PARTYSERVICE_PROTOCOL', 'http://')
    PARTYSERVICE_SERVER = os.environ.get('PARTYSERVICE_SERVER', 'localhost:8081')
    PARTYSERVICE_RESPONDENTS_ENDPOINT = os.environ.get('PARTYSERVICE_RESPONDENTS_ENDPOINT', '/collection-exercise-api/1.0.0/respondents/')
    PARTYSERVICE_BUSINESSES_ENDPOINT = os.environ.get('PARTYSERVICE_BUSINESSES_ENDPOINT', '/collection-exercise-api/1.0.0/businesses/')


class CaseService(Config):
    """
    This class is used to configure details and parameters for the CaseService microservice.
    This is temporary until an admin config feature is added to allow manual config of the microservice and/or a
    configuration management process
    """

    CASESERVICE_PROTOCOL = os.environ.get('CASESERVICE_PROTOCOL', 'http://')
    CASESERVICE_SERVER = os.environ.get('CASESERVICE_SERVER', 'localhost:8081')
    CASESERVICE_CASES_ENDPOINT = os.environ.get('CASESERVICE_CASES_ENDPOINT', '/collection-exercise-api/1.0.0/cases/')


class CollectionExerciseService(Config):
    """
    This class is used to configure details and parameters for the CollectionExerciseService microservice.
    This is temporary until an admin config feature is added to allow manual config of the microservice and/or a
    configuration management process
    """

    COLLECTIONEXERCISESERVICE_PROTOCOL = os.environ.get('COLLECTIONEXERCISESERVICE_PROTOCOL', 'http://')
    COLLECTIONEXERCISESERVICE_SERVER = os.environ.get('COLLECTIONEXERCISESERVICE_SERVER', 'localhost:8081')
    COLLECTIONEXERCISESERVICE_ENDPOINT = os.environ.get('COLLECTIONEXERCISESERVICE_ENDPOINT', '/collection-exercise-api/1.0.0/')


class SurveyService(Config):
    """
    This class is used to configure details and parameters for the SurveyService microservice.
    This is temporary until an admin config feature is added to allow manual config of the microservice and/or a
    configuration management process
    """

    SURVEYSERVICE_PROTOCOL = os.environ.get('SURVEYSERVICE_PROTOCOL', 'http://')
    SURVEYSERVICE_SERVER = os.environ.get('SURVEYSERVICE_SERVER', 'localhost:8081')
    SURVEYSERVICE_ENDPOINT = os.environ.get('SURVEYSERVICE_ENDPOINT', '/collection-exercise-api/1.0.0/surveys/')


class OAuthConfig(Config):
    """
    This class is used to configure OAuth2 parameters for the microservice.
    This is temporary until an admin config feature
    is added to allow manual config of the microservice
    """

    ONS_OAUTH_PROTOCOL = os.environ.get('ONS_OAUTH_PROTOCOL', 'http://')
    ONS_OAUTH_SERVER = os.environ.get('ONS_OAUTH_SERVER', 'localhost:8040')
    RAS_FRONTSTAGE_CLIENT_ID = os.environ.get('RAS_FRONTSTAGE_CLIENT_ID', 'ons@ons.gov')
    RAS_FRONTSTAGE_CLIENT_SECRET = os.environ.get('RAS_FRONTSTAGE_CLIENT_SECRET', 'password')
    ONS_AUTHORIZATION_ENDPOINT = os.environ.get('ONS_AUTHORIZATION_ENDPOINT', '/web/authorize/')
    ONS_TOKEN_ENDPOINT = os.environ.get('ONS_TOKEN_ENDPOINT', '/api/v1/tokens/')
    ONS_ADMIN_ENDPOINT = os.environ.get('ONS_ADMIN_ENDPOINT', '/api/account/create')


class FrontstageLogging(Config):
    """
    This class is used to set up and define logging behaviour for ras-frontstage
    """
    logger = logging.getLogger(__name__)
    SERVICE_NAME = 'ras-frontstage'
    LOG_FORMAT = 'ras-frontstage: %(asctime)s|%(levelname)s | %(name)s.%(funcName)s:%(lineno)d | %(message)s'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')                        # If we don't have a detailed logger set
                                                                            # lets just set the level as DEBUG
