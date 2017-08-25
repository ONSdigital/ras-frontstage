"""
Module to create jwt token.
"""
from datetime import datetime, timedelta
from jose import jwt

JWT_ALGORITHM = 'HS256'
JWT_SECRET = 'vrwgLNWEffe45thh545yuby'


def timestamp_token(token, username=None, party_id=None):
    """Time stamp the expires_in argument of the OAuth2 token. And replace with an expires_in UTC timestamp"""

    current_time = datetime.now()
    expires_in = current_time + timedelta(seconds=token['expires_in'])
    data_dict_for_jwt_token = {
        "refresh_token": token['refresh_token'],
        "access_token": token['access_token'],
        "scope": token['scope'],
        "expires_at": expires_in.timestamp(),
        "username": username,
        "role": "respondent",
        "party_id": party_id
    }

    return data_dict_for_jwt_token


def encode(data):
    """Encode data in jwt token."""
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode(token):
    """Decode data in jwt token."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


data_dict_for_jwt_token = {"user_id": "c3c0c2cd-bd52-428f-8841-540b1b7dd619",
                           "user_scopes": ['foo', 'bar', 'qux']}
