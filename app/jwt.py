"""
Module to create jwt token.
"""

from jose import jwt

JWT_ALGORITHM = 'HS256'
JWT_SECRET = 'vrwgLNWEffe45thh545yuby'


def encode(data):
    """Encode data in jwt token."""
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode(token):
    """Decode data in jwt token."""
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


data_dict_for_jwt_token = {"user_id": "c3c0c2cd-bd52-428f-8841-540b1b7dd619",
                           "user_scopes": ['foo', 'bar', 'qux']}
