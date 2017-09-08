import os
import logging

# If no APP_SETTINGS in environment variables use developer settings
# This has to run before triggering frontstage.__init__.py
if not os.getenv('APP_SETTINGS'):
    os.environ['APP_SETTINGS'] = 'DevelopmentConfig'

from frontstage import app  #NOQA  # pylint: disable=wrong-import-position
from frontstage.cloud.cloud_foundry import ONSCloudFoundry  #NOQA  # pylint: disable=wrong-import-position
from structlog import wrap_logger  #NOQA  # pylint: disable=wrong-import-position


logger = wrap_logger(logging.getLogger(__name__))

if __name__ == '__main__':
    cf = ONSCloudFoundry()
    # First check if front-stage is deployed in a Cloud Foundry environment
    if cf.detected:
        port = cf.port
        protocol = cf.protocol
        logger.info('* Cloud Foundry environment detected.')
        logger.info('* Cloud Foundry port "{}"'.format(port))
        logger.info('* Cloud Foundry protocol "{}"'.format(protocol))
    else:
        port = os.getenv('FS_DEV_PORT', 8080)
    logger.info('* starting listening port "{}"'.format(port))
    app.run(debug=True, host='0.0.0.0', port=int(port))
