import logging
from json import load
from os.path import join

from structlog import wrap_logger

from frontstage import app

logger = wrap_logger(logging.getLogger(__name__))


class Translate:
    def __init__(self, translation_file):
        translation_default_path = join(app.root_path, "i18n")
        self.translation_path = app.config.get("TRANSLATIONS_PATH", translation_default_path)
        default_locale = "en_GB"
        self.locale = app.config.get("DEFAULT_LOCALE", default_locale)

        try:
            if not translation_file.endswith(".json"):
                translation_file += ".json"

            file_name = join(self.translation_path, translation_file)
            with open(file_name) as f:
                self.translations = load(f)
        except FileNotFoundError as exc:
            logger.error("Instantiating translation with file failed, could not find file", file_name=file_name)
            raise exc
        except Exception as exc:
            logger.error("An error occurred loading JSON from file", file_name=file_name)
            raise exc

    def translate(self, msgid, locale=None):
        active_locale = locale if locale else self.locale

        if active_locale not in self.translations:
            logger.info("Did not find locale, returning message id", locale=active_locale, msgid=msgid)
            return msgid

        translations = self.translations[active_locale]

        if msgid not in translations:
            logger.info("Found no string for message ID in locale", msgid=msgid, locale=active_locale)
            return msgid

        if translations[msgid] is False:
            return msgid

        return translations[msgid]
