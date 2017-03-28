# ***** Oauth2 Resource Owner Password Grant *****


# This test script only works if you have the django Oauth2 Server running. It uses the libraries the ras-frontstage uses to talk to
# the Oauth2 server to fetch a token, or access code. To run this test you need to:
# 1) Please read this to setup your Oauth2 server: https://github.com/ONSdigital/django-oauth2-test
# 2) Export the environment variable OAUTHLIB_INSECURE_TRANSPORT witht the command: />  export OAUTHLIB_INSECURE_TRANSPORT=1
# 	 This is done as the dev environment is not over https



from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session

# Setup client ID, client secret, username and password variables. Thease users must exist on the django Oauth2 server
#

client_id='onc@onc.gov'
client_secret = 'password'
username = 'testuser@email.com'
password = 'password'

print " *** Variables setup ***"

# Create an OAuth session. This will handle the send and response http message, and formatting for us.


client = LegacyApplicationClient(client_id=client_id)
client.prepare_request_body(username=username, password=password, scope=['ci.write', 'ci.read'])
oauth = OAuth2Session(client=client)

print " OAuth2 Session has been created for client: {}".format(client_id)

token = oauth.fetch_token(token_url='http://localhost:8000/api/v1/tokens/', username=username, password=password, client_id=client_id, client_secret=client_secret)

print " *** Access Token Granted *** "
print " Values are: "
for key in token:
	print key, " Value is: ", token[key]
