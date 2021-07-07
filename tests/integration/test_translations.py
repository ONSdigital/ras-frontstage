from os.path import join
from unittest import TestCase
from unittest.mock import MagicMock, mock_open, patch

from frontstage import app
from frontstage.i18n.translations import Translate


class TestTranslations(TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.example_translations = {
            "en_GB": {"message1": "message_1_return", "message2": False},
            "fr_FR": {"message1": "message_1_revenir"},
            "es_ES": {},
        }

    # Constructor tests
    def test_appends_json_to_filename_if_not_included(self):
        with patch("builtins.open", new_callable=mock_open()) as m_open:
            with patch("frontstage.i18n.translations.load", MagicMock()) as m_load:
                m_load.return_value = ""

                Translate("filename")
                self.assertEqual(m_open.call_count, 1)
                self.assertTrue(m_open.call_args[0][0].endswith("filename.json"))

    def test_does_not_append_json_to_filename_if_included(self):
        with patch("builtins.open", new_callable=mock_open()) as m_open:
            with patch("frontstage.i18n.translations.load", MagicMock()) as m_load:
                m_load.return_value = ""

                Translate("filename.json")
                self.assertEqual(m_open.call_count, 1)
                self.assertTrue(m_open.call_args[0][0].endswith("filename.json"))

    def test_uses_default_path_if_not_specified(self):
        with patch("builtins.open", new_callable=mock_open()) as m_open:
            with patch("frontstage.i18n.translations.load", MagicMock()) as m_load:
                m_load.return_value = ""

                del app.config["TRANSLATIONS_PATH"]
                leading_path = join(app.root_path, "i18n")

                Translate("filename")
                self.assertEqual(m_open.call_count, 1)
                self.assertTrue(m_open.call_args[0][0].startswith(leading_path))

    def test_uses_config_path_if_specified(self):
        with patch("builtins.open", new_callable=mock_open()) as m_open:
            with patch("frontstage.i18n.translations.load", MagicMock()) as m_load:
                m_load.return_value = ""

                old_config = app.config.get("TRANSLATIONS_PATH")
                app.config["TRANSLATIONS_PATH"] = "PATH"
                Translate("filename")

                self.assertEqual(m_open.call_count, 1)
                self.assertTrue(m_open.call_args[0][0].startswith("PATH"))

                app.config["TRANSLATIONS_PATH"] = old_config

    def test_loads_json_and_assigns_to_instance(self):
        with patch("builtins.open", new_callable=mock_open()):
            with patch("frontstage.i18n.translations.load", MagicMock()) as m_load:
                m_load.return_value = "TEST VALUE"

                instance = Translate("filename.json")
                self.assertEqual(instance.translations, "TEST VALUE")

    def test_raises_not_found_exception_if_file_missing(self):
        with patch("builtins.open", new_callable=mock_open()) as m_open:
            with patch("frontstage.i18n.translations.load", MagicMock()) as m_load:
                m_load.return_value = ""
                m_open.side_effect = FileNotFoundError

                with self.assertRaises(FileNotFoundError):
                    Translate("filename.json")

    def test_raises_other_exception_if_other_exception_occurs(self):
        with patch("builtins.open", new_callable=mock_open()) as m_open:
            with patch("frontstage.i18n.translations.load", MagicMock()) as m_load:
                m_load.return_value = ""
                m_open.side_effect = Exception

                with self.assertRaises(Exception):
                    Translate("filename.json")

    # Translate function tests
    def test_should_assume_default_locale_if_no_locale_passed(self):
        with patch("builtins.open", new_callable=mock_open()):
            with patch("frontstage.i18n.translations.load", MagicMock()) as m_load:
                m_load.return_value = self.example_translations
                instance = Translate("filename")
                output = instance.translate("message1")

                self.assertEqual(output, "message_1_return")

    def test_should_use_passed_locale(self):
        with patch("builtins.open", new_callable=mock_open()):
            with patch("frontstage.i18n.translations.load", MagicMock()) as m_load:
                m_load.return_value = self.example_translations
                instance = Translate("filename")
                output = instance.translate("message1", "fr_FR")

                self.assertEqual(output, "message_1_revenir")

    def test_should_return_message_id_if_passed_locale_is_not_in_translations(self):
        with patch("builtins.open", new_callable=mock_open()):
            with patch("frontstage.i18n.translations.load", MagicMock()) as m_load:
                m_load.return_value = self.example_translations
                instance = Translate("filename")
                output = instance.translate("message1", "de")

                self.assertEqual(output, "message1")

    def test_should_return_message_id_if_translation_is_false(self):
        with patch("builtins.open", new_callable=mock_open()):
            with patch("frontstage.i18n.translations.load", MagicMock()) as m_load:
                m_load.return_value = self.example_translations
                instance = Translate("filename")
                output = instance.translate("message2", "en")

                self.assertEqual(output, "message2")

    def test_should_message_id_if_passed_locale_exists_but_doesnt_contain_message_id(self):
        with patch("builtins.open", new_callable=mock_open()):
            with patch("frontstage.i18n.translations.load", MagicMock()) as m_load:
                m_load.return_value = self.example_translations
                instance = Translate("filename")
                output = instance.translate("message3", "en")

                self.assertEqual(output, "message3")
