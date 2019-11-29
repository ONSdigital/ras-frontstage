import requests
from flask import current_app


class Requests:

    _lib = requests

    @staticmethod
    def get_timeout():
        return int(current_app.config['REQUESTS_GET_TIMEOUT'])

    @staticmethod
    def post_timeout():
        return int(current_app.config['REQUESTS_POST_TIMEOUT'])

    @staticmethod
    def auth():
        return current_app.config['SECURITY_USER_NAME'], current_app.config['SECURITY_USER_PASSWORD']

    @classmethod
    def get(cls, *args, **kwargs):
        try:
            auth = kwargs.pop('auth')
        except KeyError:
            auth = cls.auth()
        return cls._lib.get(*args, auth=auth, timeout=cls.get_timeout(), **kwargs)

    @classmethod
    def put(cls, *args, **kwargs):
        try:
            auth = kwargs.pop('auth')
        except KeyError:
            auth = cls.auth()
        return cls._lib.put(*args, auth=auth, timeout=cls.post_timeout(), **kwargs)

    @classmethod
    def post(cls, *args, **kwargs):
        try:
            auth = kwargs.pop('auth')
        except KeyError:
            auth = cls.auth()
        return cls._lib.post(*args, auth=auth, timeout=cls.post_timeout(), **kwargs)
