import requests

from frontstage import app


def get_respondent_by_email(email):

    url = f'{app.config["PARTY_URL"]}/party-api/v1/respondents/email'
    response = requests.get(url, json={"email": email}, auth=(app.config['PARTY_USERNAME'],
                                                              app.config['PARTY_PASSWORD']))

    if response.status_code == 404:
        return 'Respondent not found'
    response.raise_for_status()

    return response.json()
