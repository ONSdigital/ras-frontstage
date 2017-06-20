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
    CSRF_ENABLED = False
    # WTF_CSRF_CHECK_DEFAULT = False
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'this-really-needs-to-be-changed'
    dbname = "ras_frontstage_backup"
    # SQLALCHEMY_DATABASE_URI = "postgresql://" + dbname + ":password@localhost:5431/postgres"
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'postgresql://ras_frontstage_backup:password@localhost:5431/postgres')

    # API_GATEWAY_SURVEYS_URL = 'https://api-dev.apps.mvp.onsclofo.uk/api/1.0.0/surveys/'
    API_GATEWAY_SURVEYS_URL='http://localhost:8050/api/my-surveys/'

    API_GATEWAY_COLLECTION_INSTRUMENT_URL = 'https://api-dev.apps.mvp.onsclofo.uk:443/collection-instrument-api/1.0.2/'
    API_GATEWAY_PARTY_URL = 'https://api-dev.apps.mvp.onsclofo.uk/party-api/1.0.4/'


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
