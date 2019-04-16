from unittest import TestCase
from unittest.mock import patch, mock_open, MagicMock

from frontstage.i18n.translations import Translate


class TestTranslations(TestCase):

    def setUp(self):
        self.mock_open = mock_open()

    # Constructor tests
    def test_appends_json_to_filename_if_not_included(self):
        with patch('builtins.open', new_callable=mock_open()) as m:
            with patch('frontstage.i18n.translations.load', MagicMock()) as loadd:
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

