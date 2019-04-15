import unittest

from frontstage import app
from frontstage.jwt import encode, decode

data_dict_for_jwt_token = {
    'refresh_token': 'e6bde0f6-e123-4dcf-9567-74f4d072fc71',
    'access_token': 'f418d491-eeda-47cb-b3e3-0d5d7b97ee6d',
    'username': 'johndoe',
    'expires_at': '100123456789',
    'scope': '[foo,bar,qnx]'

}
encoded_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyZWZyZXNoX3Rva2VuIjoiZTZiZGUwZjYtZTEyMy00ZGNmLTk1NjctNzRmNGQ' \
                'wNzJmYzcxIiwiYWNjZXNzX3Rva2VuIjoiZjQxOGQ0OTEtZWVkYS00N2NiLWIzZTMtMGQ1ZDdiOTdlZTZkIiwidXNlcm5hbWUiOiJ' \
                'qb2huZG9lIiwic2NvcGUiOiJbZm9vLGJhcixxbnhdIiwiZXhwaXJlc19hdCI6IjEwMDEyMzQ1Njc4OSJ9.NhOb7MK_SaaW8wvqwb' \
                'iiAv5N-oaN8SHYli2Z-NpkJ2A'


class TestApplication(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.headers = {
            "Authorization": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoicmluZ3JhbUBub3d3aGVyZS5jb20iLCJ1c2VyX3Njb3BlcyI6WyJjaS5yZWFkIiwiY2kud3JpdGUiXX0.se0BJtNksVtk14aqjp7SvnXzRbEKoqXb8Q5U9VVdy54"  # NOQA
        }

    def test_encode_jwt(self):
        my_encoded_dictionary = encode(data_dict_for_jwt_token)
        my_decoded_dictionary = decode(my_encoded_dictionary)
        self.assertEqual(my_decoded_dictionary, data_dict_for_jwt_token)
