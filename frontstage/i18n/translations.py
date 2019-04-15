import logging
from json import load
from structlog import wrap_logger
from frontstage import app
from os.path import join

logger = wrap_logger(logging.getLogger(__name__))

translation_default_path = join(app.root_path, 'i18n')
translation_path = app.config.get('TRANSLATIONS_PATH', translation_default_path)
default_locale = 'en_GB'
locale = app.config.get('DEFAULT_LOCALE', default_locale)


class Translate:

    def __init__(self, translation_file):
        try:
            if not translation_file.endswith('.json'):
                translation_file += '.json'

            file_name = join(translation_path, translation_file)
            with open(file_name) as f:
                self.translations = load(f)
        except FileNotFoundError as exc:
            logger.error(f'Instantiating translation with file {file_name}')
            raise(exc)
        except Exception as exc:
            logger.error(f'An error occurred loading JSON from file {file_name}')
            raise(exc)

    def translate(self, msgid, locale=default_locale):

        active_locale = locale if locale in self.translations else default_locale

        if active_locale not in self.translations:
            logger.debug(f'Defaulted to default locale for {msgid} because locale {locale} had message with that Id')
            return msgid

        translations = self.translations[active_locale]

        if msgid not in translations:
            logger.debug(f'Found no string for message ID {msgid} in locale {locale}')
            return msgid

        return translations[msgid]

