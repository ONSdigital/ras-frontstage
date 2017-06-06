"""
Module to generate jwt token
"""

from jose import jwt
from app import settings

JWT_ALGORITHM = 'HS256'
JWT_SECRET = settings.JWT_SECRET


def encode(data):
    """
    Function to encode python dict data
    """
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM, headers={"alg": JWT_ALGORITHM, 'typ': 'jwt'})


def decode(token):
    """
    Function to decode python dict data
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
