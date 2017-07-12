import unittest
from app.application import app
from app.jwt import encode, decode
from app.config import OAuthConfig, Config
import json
import requests_mock

with open('tests/test_data/my_surveys.json') as json_data:
    my_surveys_data = json.load(json_data)

returned_token = {
    "id": 6,
    "access_token": "a712f0f9-d00d-447a-b143-49984ca3db68",
    "expires_in": 3600,
    "token_type": "Bearer",
    "scope": "",
    "refresh_token": "37ca04d2-6b6c-4854-8e85-f59c2cc7d3de"
}

data_dict_for_jwt_token = {
    'refresh_token': 'e6bde0f6-e123-4dcf-9567-74f4d072fc71',
    'access_token': 'f418d491-eeda-47cb-b3e3-0d5d7b97ee6d',
    'username': 'johndoe',
    'expires_at': '100123456789',
    'scope': '[foo,bar,qnx]'
}

party_id = "3b136c4b-7a14-4904-9e01-13364dd7b972"

test_user = {
    'first_name': 'john',
    'last_name': 'doe',
    'email_address': 'testuser2@email.com',
    'password': 'password',
    'password_confirm': 'password',
    'phone_number': '07717275049'
}

data_dict_zero_length = {"": ""}

encoded_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyZWZyZXNoX3Rva2VuIjoiZTZiZGUwZjYtZTEyMy00ZGNmLTk1NjctNzRmNGQwNzJmYzcxIiwiYWNjZXNzX3Rva2VuIjoiZjQxOGQ0OTEtZWVkYS00N2NiLWIzZTMtMGQ1ZDdiOTdlZTZkIiwidXNlcm5hbWUiOiJqb2huZG9lIiwic2NvcGUiOiJbZm9vLGJhcixxbnhdIiwiZXhwaXJlc19hdCI6IjEwMDEyMzQ1Njc4OSJ9.NhOb7MK_SaaW8wvqwbiiAv5N-oaN8SHYli2Z-NpkJ2A'


class TestApplication(unittest.TestCase):
    # TODO reinstate tests after horrific merge problem

    def setUp(self):

        self.app = app.test_client()
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
            }
