import unittest

from application.app import validate_uri


class TestApplication(unittest.TestCase):

    def test_valid_uri(self):
        uri = "urn:ons.gov.uk:id:survey:001.001.00001"
        self.assertEquals(validate_uri(uri, "survey"), True)

    def test_invalid_uri(self):
        uri = "ons.gov.uk:id:survey:001.001.00001"
        self.assertEquals(validate_uri(uri, "survey"), False)
