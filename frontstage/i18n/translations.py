import logging
from json import load
from sys import locale
from structlog import wrap_logger
from frontstage import app
from os.path import join

logger = wrap_logger(logging.getLogger(__name__))

translation_default_path = join(app.instance_path, 'i18n')
translation_path = app.config.get('TRANSLATIONS_PATH', translation_default_path)



class Translate:

    def __init__(self, translation_file):
        try:
            if not translation_file.endsWith('.json'):
                translation_file += '.json'

            file = join(translation_path, translation_file)
            with open(file) as f:
                self.translations = load(f)
        except FileNotFoundError:
            logger.error(f'Instantiating translation with file {file}')
        except Exception:
            logger.error(f'An error occurred loading JSON from file {file}')

    def translate(self, msgid):
        try:
            translation = self.translations[locale][msgid]
        except KeyError:
            logger.debug(f'Found no string for message ID in {file} using ID {msgid}')
            translation = msgid

        return translation

