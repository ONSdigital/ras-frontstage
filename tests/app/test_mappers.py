import unittest

from iso8601 import ParseError

from frontstage.common.mappers import convert_events_to_new_format
from tests.app.mocked_services import collection_exercise


class TestMappers(unittest.TestCase):

    def test_convert_events_to_new_format_successful(self):
        formatted_events = convert_events_to_new_format(collection_exercise['events'])

        self.assertTrue(formatted_events['go_live'] is not None)
        self.assertTrue(formatted_events['go_live']['day'] is not None)
        self.assertTrue(formatted_events['go_live']['date'] is not None)
        self.assertTrue(formatted_events['go_live']['month'] is not None)
        self.assertTrue(formatted_events['go_live']['time'] is not None)
        self.assertTrue(formatted_events['go_live']['is_in_future'] is not None)

    def test_convert_events_to_new_format_fail(self):
        events = [{
            "timestamp": "abc"
        }]

        with self.assertRaises(ParseError):
            convert_events_to_new_format(events)
