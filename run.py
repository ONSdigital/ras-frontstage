import os
import logging

# If no APP_SETTINGS in environment variables use developer settings
# This has to run before triggering frontstage.__init__.py
if not os.getenv('APP_SETTINGS'):
    os.environ['APP_SETTINGS'] = 'DevelopmentConfig'

from frontstage import app  # NOQA  # pylint: disable=wrong-import-position
from structlog import wrap_logger  # NOQA  # pylint: disable=wrong-import-position


logger = wrap_logger(logging.getLogger(__name__))

if __name__ == '__main__':
    port = os.getenv('FS_DEV_PORT', 8082)
    logger.info('* starting listening port "{}"'.format(port))
    app.run(debug=True, host='0.0.0.0', port=int(port))
