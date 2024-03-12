"""
Module to create jwt token.
"""
import jwt

from frontstage import app


def encode(data):
    """Encode data in jwt token."""
    return jwt.encode(data, app.config["JWT_SECRET"], algorithm="HS256")


def decode(token):
    """Decode data in jwt token."""
    return jwt.decode(token, app.config["JWT_SECRET"], algorithms=["HS256"])
