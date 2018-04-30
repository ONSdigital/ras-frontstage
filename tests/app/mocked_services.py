import json

from frontstage import app


with open('tests/test_data/party/party.json') as json_data:
	party = json.load(json_data)


url_oauth_token = f"{app.config['OAUTH_SERVICE_URL']}/api/v1/tokens/"
url_get_party_email = f"{app.config['PARTY_SERVICE_URL']}/party-api/v1/respondents/email"
