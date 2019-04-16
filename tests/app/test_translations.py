from os.path import join
from unittest import TestCase
from unittest.mock import patch, mock_open, MagicMock

from frontstage.i18n.translations import Translate
from frontstage import app


class TestTranslations(TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    # Constructor tests
    def test_appends_json_to_filename_if_not_included(self):
        with patch('builtins.open', new_callable=mock_open()) as m_open:
            with patch('frontstage.i18n.translations.load', MagicMock()) as m_load:
                m_load.return_value = ''

                Translate('filename')
                self.assertEqual(m_open.call_count, 1)
                self.assertTrue(m_open.call_args[0][0].endswith('filename.json'))

    def test_does_not_append_json_to_filename_if_included(self):
        with patch('builtins.open', new_callable=mock_open()) as m_open:
            with patch('frontstage.i18n.translations.load', MagicMock()) as m_load:
                m_load.return_value = ''

                Translate('filename.json')
                self.assertEqual(m_open.call_count, 1)
                self.assertTrue(m_open.call_args[0][0].endswith('filename.json'))

    def test_uses_default_path_if_not_specified(self):
        with patch('builtins.open', new_callable=mock_open()) as m_open:
            with patch('frontstage.i18n.translations.load', MagicMock()) as m_load:
                m_load.return_value = ''

                leading_path = join(app.root_path, 'i18n')

                Translate('filename')
                self.assertEqual(m_open.call_count, 1)
                self.assertTrue(m_open.call_args[0][0].startswith(leading_path))

    def test_uses_config_path_if_specified(self):
        with patch('builtins.open', new_callable=mock_open()) as m_open:
            with patch('frontstage.i18n.translations.load', MagicMock()) as m_load:
                m_load.return_value = ''

                app.config['TRANSLATIONS_PATH'] = 'PATH'
                Translate('filename')

                self.assertEqual(m_open.call_count, 1)
                self.assertTrue(m_open.call_args[0][0].startswith('PATH'))

    def test_loads_json_and_assigns_to_instance(self):
        with patch('builtins.open', new_callable=mock_open()) as m_open:
            with patch('frontstage.i18n.translations.load', MagicMock()) as m_load:
                m_load.return_value = 'TEST VALUE'

                instance = Translate('filename.json')
                self.assertEqual(instance.translations, 'TEST VALUE')

    def test_raises_not_found_exception_if_file_missing(self):
        with patch('builtins.open', new_callable=mock_open()) as m_open:
            with patch('frontstage.i18n.translations.load', MagicMock()) as m_load:
                m_load.return_value = ''
                m_open.side_effect = FileNotFoundError

                with self.assertRaises(FileNotFoundError):
                    Translate('filename.json')

    def test_raises_other_exception_if_other_exception_occurs(self):
        with patch('builtins.open', new_callable=mock_open()) as m_open:
            with patch('frontstage.i18n.translations.load', MagicMock()) as m_load:
                m_load.return_value = ''
                m_open.side_effect = Exception

                with self.assertRaises(Exception):
                    Translate('filename.json')

