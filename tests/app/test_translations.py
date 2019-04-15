from unittest import TestCase
from unittest.mock import patch, mock_open

from frontstage.i18n.translations import Translate

from os.path import join
from json import load


class TestTranslations(TestCase):

    def setUp(self):
        self.mock_load = patch('frontstage.i18n.translations.load')

    # Constructor tests
    def test_appends_json_to_filename_if_not_included(self):
        self.mock_load.return_value = ''
        m = mock_open(read_data='')
        with patch('frontstage.i18n.translations.open', m, create=True):
            instance = Translate('filename')
            self.assertEqual(True, instance)

    def test_does_not_append_json_to_filename_if_included(self):
        pass

    def test_uses_default_path_if_not_specified(self):
        pass

    def test_uses_config_path_if_specified(self):
        pass

    def test_loads_json_and_assigns_to_instance(self):
        pass

    def test_logs_and_raises_not_found_exception_if_file_missing(self):
        pass

    def test_logs_and_raises_other_exception_if_other_exception_occurs(self):
        pass

