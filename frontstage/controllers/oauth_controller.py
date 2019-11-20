import logging
# from json import JSONDecodeError, dumps

import requests
from flask import current_app as app
# from requests import HTTPError
from structlog import wrap_logger

from frontstage.exceptions.exceptions import ApiError, OAuth2Error


logger = wrap_logger(logging.getLogger(__name__))


def sign_in(username, password):
    logger.info('Attempting to retrieve OAuth2 token for sign-in')

    url = f"{app.config['OAUTH_URL']}/api/v1/tokens/"
    data = {
        'grant_type': 'password',
        'client_id': app.config['OAUTH_CLIENT_ID'],
        'client_secret': app.config['OAUTH_CLIENT_SECRET'],
        'username': username,
        'password': password,
    }
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
    }
    response = requests.post(url, headers=headers, auth=app.config['OAUTH_BASIC_AUTH'], data=data)

    try:
        response.raise_for_status()
        # This if statement will only be true if the 'oauth' service is the ras-rm-auth-service.  This is only
        # meant to be a temporary measure until the switch is made and the new auth service is used.  Once
        # the oauth2 service is switched off, we should look to tidy up the api of the auth service (As the service
        # doesn't need a /tokens endpoint if there are no tokens) and tidy up this services interaction with it.
        if response.status_code == 204:
            return {}
    except requests.exceptions.HTTPError:
        if response.status_code == 401:
            auth_error = response.json().get('detail', '')
            message = response.json().get('title', '')

            raise OAuth2Error(logger, response, log_level='warning', message=message, oauth2_error=auth_error)
        else:
            logger.error('Failed to retrieve OAuth2 token')
            raise ApiError(logger, response)

    logger.info('Successfully retrieved OAuth2 token')
    return response.json()

#
# def login_admin():
#     headers = {'Content-Type': 'application/x-www-form-urlencoded',
#                'Accept': 'application/json'}
#     payload = {'grant_type': 'client_credentials',
#                'response_type': 'token',
#                'token_format': 'opaque'}
#     try:
#         url = f"{app.config['OAUTH_URL']}/oauth/token"
#         response = requests.post(url, headers=headers, params=payload,
#                                  auth=(app.config['OAUTH_CLIENT_ID'], app.config['OAUTH_CLIENT_SECRET']))
#         resp_json = response.json()
#         return resp_json.get('access_token')
#     except HTTPError:
#         logger.exception(f'Failed to log into OAUTH', status_code=response.status_code)
#         abort(response.status_code)
#
#
# def get_user_by_email(email, access_token=None):
#     if access_token is None:
#         access_token = login_admin()
#
#     headers = {'Content-Type': 'application/json',
#                'Accept': 'application/json',
#                'Authorization': f'Bearer {access_token}'}
#
#     url = f"{app.config['OAUTH_URL']}/Users?filter=email+eq+%22{email}%22"
#     response = requests.get(url, headers=headers)
#     if response.status_code != 200 or response.json()['totalResults'] == 0:
#         return
#
#     return response.json()
#
#
# def get_first_name_by_email(email):
#     response = get_user_by_email(email)
#     if response is not None:
#         return response['resources'][0]['name']['givenName']
#     return ""
#
#
# def retrieve_user_code(access_token, username):
#     headers = {'Content-Type': 'application/json',
#                'Accept': 'application/json',
#                'Authorization': f'Bearer {access_token}'}
#
#     url = f"{app.config['OAUTH_URL']}/password_resets"
#     response = requests.post(url, headers=headers, data=username)
#
#     if response.status_code != 201:
#         logger.error('Error received when asking OAUTH for a password reset code',
#                      status_code=response.status_code)
#         return
#
#     return response.json().get('code')
#
#
# def change_password(access_token, user_code, new_password):
#     headers = {'Content-Type': 'application/json',
#                'Accept': 'application/json',
#                'Authorization': f'Bearer {access_token}'}
#
#     payload = {
#         "code": user_code,
#         "new_password": new_password
#     }
#
#     url = f"{app.config['OAUTH_URL']}/password_change"
#     return requests.post(url, data=dumps(payload), headers=headers)
#
#
# def change_user_password(email, password):
#     access_token = login_admin()
#
#     user_response = get_user_by_email(email, access_token)
#     if user_response is None:
#         return
#     username = user_response['resources'][0]['userName']
#
#     password_reset_code = retrieve_user_code(access_token=access_token, username=username)
#     if password_reset_code is None:
#         return
#
#     return change_password(access_token=access_token, user_code=password_reset_code,
#                            new_password=password)
