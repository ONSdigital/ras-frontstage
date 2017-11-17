"""
Module to create jwt token.
"""
from datetime import datetime, timedelta

from jose import jwt

from frontstage import app


def timestamp_token(token):
    """Time stamp the expires_in argument of the OAuth2 token. And replace with an expires_in UTC timestamp"""

    current_time = datetime.now()
    expires_in = current_time + timedelta(seconds=token['expires_in'])
    data_dict_for_jwt_token = {
        "refresh_token": token['refresh_token'],
        "access_token": token['access_token'],
        "role": "respondent",
        "party_id": token['party_id']
    }

    return data_dict_for_jwt_token


def encode(data):
    """Encode data in jwt token."""
    return jwt.encode(data, app.config['JWT_SECRET'], algorithm=app.config['JWT_ALGORITHM'])


def decode(token):
    """Decode data in jwt token."""
    return jwt.decode(token, app.config['JWT_SECRET'], algorithms=[app.config['JWT_ALGORITHM']])
