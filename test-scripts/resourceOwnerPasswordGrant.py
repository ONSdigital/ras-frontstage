# ***** Oauth2 Resource Owner Password Grant *****


# This test script only works if you have the django Oauth2 Server running. It uses the libraries the ras-frontstage uses to talk to
# the Oauth2 server to fetch a token, or access code. To run this test you need to:
# 1) Please read this to setup your Oauth2 server: https://github.com/ONSdigital/django-oauth2-test
# 2) Export the environment variable OAUTHLIB_INSECURE_TRANSPORT witht the command: />  export OAUTHLIB_INSECURE_TRANSPORT=1
# 	 This is done as the dev environment is not over https


from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session


# Setup client ID, client secret, username and password variables. Thease users must exist on the django Oauth2 server
#

class Config(object):
    """
    Base config class
    """
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'this-really-needs-to-be-changed'
    dbname = "ras_frontstage_backup"
    SQLALCHEMY_DATABASE_URI = "postgresql://" + dbname + ":password@localhost:5431/postgres"


class OAuthConfig(Config):
    """
    This class is used to configure OAuth2 parameters for the microservice.
    This is temporary until an admin config feature
    is added to allow manual config of the microservice
    """
    APP_ID = "399360140422360"  # This is an APP ID registered with the Facebook OAuth2

    # App secret for a test registered Facebook OAuth2
    APP_SECRET = "8daae4110e491db2c5067e5c89add2dd"

    DISPLAY_NAME = "NoisyAtom"  # This is a test name registered with Facebook OAuth2
    REDIRECT_ENDPOINT = ["http://104.236.14.123:8002/auth/callback",
                         "http://104.236.14.123:8002/auth/callback.html"]

    AUTHORIZATION_ENDPOINT = "https://www.facebook.com/dialog/oauth"  # Facebook Auth endpoint
    TOKEN_ENDPOINT = "https://graph.facebook.com/oauth/access_token"  # Facebook token endpoint

    ONS_OAUTH_SERVER = "localhost:8000"
    RAS_FRONTSTAGE_CLIENT_ID = "onc@onc.gov"
    RAS_FRONTSTAGE_CLIENT_SECRET = "password"
    ONS_AUTHORIZATION_ENDPOINT = "/web/authorize/"
    ONS_TOKEN_ENDPOINT = "/api/v1/tokens/"


client_id = 'onc@onc.gov'
client_secret = 'password'
username = 'testuser@email.com'
password = 'password'

print(" *** Variables setup ***")

# print Config.DEBUG
# print OAuthConfig.RAS_FRONTSTAGE_CLIENT_ID

# Create an OAuth session. This will handle the send and response http message, and formatting for us.


client = LegacyApplicationClient(client_id=client_id)
client.prepare_request_body(username=username, password=password, scope=['ci.write', 'ci.read'])
oauth = OAuth2Session(client=client)

print(" OAuth2 Session has been created for client: {}".format(client_id))

token = oauth.fetch_token(token_url='http://localhost:8000/api/v1/tokens/', username=username, password=password, client_id=client_id, client_secret=client_secret)

print(" *** Access Token Granted *** ")
print(" Values are: ")
for key in token:
    print(key, " Value is: ", token[key])
